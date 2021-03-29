# -*- coding: utf-8 -*-
"""A Tarbell blueprint that publishes to P2P"""

import os
import locale

from clint.textui import colored
from flask import g, render_template
import ftfy
from jinja2.exceptions import TemplateNotFound
import markdown
import shutil
from simplejson.scanner import JSONDecodeError
from tarbell.hooks import register_hook
from tarbell.utils import puts

import p2p

from tribune_viztools.tarbell.blueprint import TribuneTarbellBlueprint
from tribune_viztools.tarbell.hooks import (
    copy_front_end_build_script_templates,
    create_front_end_files,
    create_readme,
    create_unfuddle_project,
    newproject_add_excludes,
    merge_extra_context,
    newproject_share_spreadsheet,
)

NAME = "Chicago Tribune DataViz: P2P"
P2P_DATA_KICKER_ID = 3681
CONTENT_ITEMS_WORKSHEET = 'p2p_content_items'

blueprint = TribuneTarbellBlueprint('blueprint', __name__)

try:
    locale.setlocale(locale.LC_ALL, 'en_US')
except locale.Error:
    puts(colored.red("Locale error"))

# Since we're importing some Tarbell hook functions from the
# tribune_viztools packages, we'll register them by calling
# `register_hook(hook_function)` instead of using
# register_hook as a decorator

# These will be registered with the `newproject` hook
NEWPROJECT_HOOKS = (
    create_front_end_files,
    copy_front_end_build_script_templates,
    create_readme,
    create_unfuddle_project,
    newproject_add_excludes,
    newproject_share_spreadsheet
)

# These will be registered with the `generate` hook
GENERATE_HOOKS = (
    merge_extra_context,
)

# These will be registered with the `publish` hook
PUBLISH_HOOKS = [
]

for f in NEWPROJECT_HOOKS:
    register_hook('newproject')(f)

for f in GENERATE_HOOKS:
    register_hook('generate')(f)

for f in PUBLISH_HOOKS:
    register_hook('publish')(f)


# Custom routes

@blueprint.app_context_processor
def add_default_htmlstory():
    """Make sure there's an htmlstory in the context for default preview"""
    site = g.current_site
    context = site.get_context()

    try:
        htmlstory = get_deprecated_htmlstory_config(context)

    except KeyError:
        htmlstory = next(s for s in context[CONTENT_ITEMS_WORKSHEET]
                         if s['content_type'] == 'htmlstory')

    return dict(htmlstory=htmlstory)


@blueprint.route('/blurbs/<p2p_slug>')
def preview_blurb(p2p_slug):
    """Locally preview a blurb"""

    site = g.current_site
    context = site.get_context()

    blurb = next(b for b in context[CONTENT_ITEMS_WORKSHEET] if b['p2p_slug'] == p2p_slug)
    return render_template(blurb['template'], blurb=blurb, **context)


@blueprint.route('/htmlstories/<p2p_slug>')
def preview_html_story(p2p_slug):
    """
    Locally preview an HTML story

    Fake the NGUX layout, headers and typography to give you an idea of what
    your project will look like on www.chicagotribune.com.

    """

    site = g.current_site
    context = site.get_context()

    htmlstory = next(s for s in context[CONTENT_ITEMS_WORKSHEET] if s['p2p_slug'] == p2p_slug)
    return render_template('index.html',
        htmlstory_template=htmlstory['template'],
        htmlstory=htmlstory, **context)


@blueprint.route('/htmlstories/<p2p_slug>/raw')
def preview_html_story_raw(p2p_slug):
    """
    Locally preview an HTML story

    Show only the HTML that will be pushed into P2P.

    This might be weird in the browser because there is no <body> tag.

    """

    site = g.current_site
    context = site.get_context()

    htmlstory = next(s for s in context[CONTENT_ITEMS_WORKSHEET] if s['p2p_slug'] == p2p_slug)
    return render_template(htmlstory['template'],
        htmlstory=htmlstory, **context)


# Helpers


def is_production_bucket(bucket_url, buckets):
    """
    Returns True if bucket_url represents the production bucket

    Args:
        bucket_url (str): URL to S3 bucket
        buckets (list): List of bucket configurations, from the Tarbell site's
            config

    Returns:
        True if bucket_url represents the production bucket.

    """
    for name, url in buckets.items():
        if url == bucket_url and name == 'production':
            return True

    return False


def render_p2p_content_item(content_item, site):
    """
    Render a P2P content item using Flask

    Args:
        content_item (dict): P2P content item metadata from your project's
            p2p_content_items worksheet.
        site (TarbellSite): Tarbell site instance.

    Returns:
        String containing rendered HTML.

    """
    # Use the technique from Frozen-Flask to use our local preview views
    # to render our templates
    # See
    # https://github.com/Frozen-Flask/Frozen-Flask/blob/master/flask_frozen/__init__.py#L267

    # First, get the URL path for the content item based on the slug
    content_type = content_item['content_type']
    if content_type == 'htmlstory':
        # We use the `raw` view because we don't want to mock
        # page chrome
        path = '/htmlstories/{p2p_slug}/raw'.format(
            p2p_slug=content_item['p2p_slug'])
    elif content_type == 'blurb':
        path = '/blurbs/{p2p_slug}'.format(
            p2p_slug=content_item['p2p_slug'])
    else:
        raise ValueError("Unknown P2P content type '{0}'".format(
            content_type))


    # Now request our view using the text client
    client = site.app.test_client()
    base_url = site.app.config['FREEZER_BASE_URL']
    response = client.get(path, base_url=base_url)

    if response.status_code != 200:
        raise ValueError("Unexpected status {0} on path {1}".format(
            response.status_code, path))

    rendered = response.data

    #if u'“' in rendered or u'”' in rendered:
            # HACK: Work around P2P API's weird handling of curly quotes where it
            # converts the first set to HTML entities and converts the rest to
            # upside down quotes
            #msg = ("Removing curly quotes because it appears that the P2P API does "
                   #"not handle them correctly.")
            #puts("\n" + colored.red(msg))
            #rendered = ftfy.fix_text(rendered, uncurl_quotes=True)

    return rendered


class MissingP2PContentItemFieldError(KeyError):
    """Exception for when a P2P content item doesn't have the required fields"""

    def __init__(self, field_name):
        msg = "P2P content item is missing field {0}".format(field_name)
        super(MissingP2PContentItemFieldError, self).__init__(msg)
        self.field_name = field_name


def p2p_publish_blurb(blurb, site, s3):
    """Publish a blurb to P2P"""

    content = render_p2p_content_item(blurb, site)

    content_item = {
        'content_item_type_code': 'blurb',
        'body': content,
        'title': blurb.get('title', ""),
        'seo_keyphrase': blurb.get('keywords', ""),
    }

    required_fields = (
        ('p2p_slug', 'slug'),
    )
    for spreadsheet_field_name, content_item_field_name in required_fields:
        try:
            content_item[content_item_field_name] = blurb[spreadsheet_field_name]
        except KeyError:
            raise MissingP2PContentItemFieldError(spreadsheet_field_name)

    try:
        p2p_conn = p2p.get_connection()
        created, response = p2p_conn.create_or_update_content_item(content_item)
        if created:
            # If we just created the item, set its state to 'working'
            p2p_conn.update_content_item({
                'slug': blurb['p2p_slug'],
                'content_item_state_code': 'working',
            })
    except JSONDecodeError:
        # HACK: Something is borked with either python-p2p or the P2P content services
        # API itself. It's ok to ignore this error
        puts("\n" + colored.yellow(
             "JSONDecodeError! when publishing to P2P. This is probably OK"))


    puts("\n" + colored.green("Published blurb to P2P with slug {}".format(blurb['p2p_slug'])))


def p2p_publish_htmlstory(htmlstory, site, s3):
    content = render_p2p_content_item(htmlstory, site)

    content_item = {
        'content_item_type_code': 'htmlstory',
        'body': content,
        'custom_param_data': {},
    }

    # TODO: The logic for renaming and transforming fields from the
    # spreadsheet to the content item data sent in the API request
    # could be refactored into a separate function and standardized
    # between the blurb and htmlstory publishing functions.
    required_fields = (
        ('p2p_slug', 'slug'),
        ('title', 'title'),
        ('byline', 'byline'),
        ('seotitle', 'seotitle'),
        ('seodescription', 'seodescription'),
        ('keywords', 'seo_keyphrase'),
    )
    for spreadsheet_field_name, content_item_field_name in required_fields:
        try:
            content_item[content_item_field_name] = htmlstory[spreadsheet_field_name]
        except KeyError:
            raise MissingP2PContentItemFieldError(spreadsheet_field_name)

    try:
        content_item['custom_param_data']['story-summary'] = markdown.markdown(htmlstory['story_summary'])
    except KeyError:
        raise MissingP2PContentItemFieldError('story_summary')

    try:
        context = site.get_context()
        base_url = "http://{0}/".format(context['ROOT_URL'])
        content_item['original_thumbnail_url'] = base_url + htmlstory['thumbnail']
        content_item['thumbnail_source_code'] = 'chicagotribune'
    except KeyError:
        # `thumbnail` value not found in data from spreadsheet
        raise MissingP2PContentItemFieldError('thumbnail')

    try:
        p2p_conn = p2p.get_connection()

        created, response = p2p_conn.create_or_update_content_item(content_item)
        if created:
            # If we just created the item, set its state to 'working'
            p2p_conn.update_content_item({
                'slug': htmlstory['p2p_slug'],
                'content_item_state_code': 'working',
                'kicker_id': P2P_DATA_KICKER_ID,
            })

    except JSONDecodeError:
        # HACK: Something is borked with either python-p2p or the P2P content services
        # API itself. It's ok to ignore this error
        puts("\n" + colored.yellow(
             "JSONDecodeError! when publishing to P2P. This is probably OK"))

    puts("\n" + colored.green(
        "Published to HTML story to P2P with slug {}".format(htmlstory['p2p_slug'])))


# Custom hooks

@register_hook('newproject')
def copy_templates(site, git):
    """
    Copy custom templates from blueprint to new project

    This is needed because Tarbell ignores the templates that start with
    '_' when copying template files from the blueprint.

    """
    filenames = [
      "_content.html",
      "_htmlstory.html",
    ]

    for filename in filenames:
        path = os.path.join(site.path, '_blueprint', filename)
        shutil.copy2(path, site.path)

# Deprecated
# This should be removed once people get used to the new p2p_content_items
# worksheet.
def get_deprecated_htmlstory_config(context):
    """
    Get the P2P properties from the values worksheet.

    This makes the blueprint backward compatible with how we used to get
    the P2P content item properties from the `values` worksheet of the
    Tarbell spreadsheet.

    We now read this from rows of the `p2p_content_items` worksheet of the
    Tarbell spreadsheet in order to support publishing multiple content
    items from one Tarbell project.


    Args:
        context (dict): Tarbell site context.

    Returns:
        Dictionary that can be passed to `p2p_publish_htmlstory`
        to construct a request to the P2P API
        to create or update an HTML story content item.

    Raises:
        KeyError if the keys aren't defined.

    """

    htmlstory = {}

    required_fieldnames = (
            ('p2p_slug', 'p2p_slug'),
    )

    optional_fieldnames = (
            ('headline', 'title'),
            ('seotitle', 'seotitle'),
            ('seodescription', 'seodescription'),
            ('keywords', 'keywords'),
            ('byline', 'byline'),
            ('story_summary', 'story_summary'),
    )

    for spreadsheet_field_name, output_field_name in required_fieldnames:
        htmlstory[output_field_name] = context[spreadsheet_field_name]

    for spreadsheet_field_name, output_field_name in optional_fieldnames:
        htmlstory[output_field_name] = context.get(spreadsheet_field_name, '')

    return htmlstory


def p2p_publish_content_items(site, s3):
    if not is_production_bucket(s3.bucket, site.project.S3_BUCKETS):
        puts(colored.red(
            "\nNot publishing to production bucket. Skipping P2P publiction."))
        return

    context = site.get_context(publish=True)

    # Handle old-style configuration for publishing HTML story from values
    # worksheet. This is deprecated, but still support it in case someone
    # accidentally upgrades their blueprint in an old project
    try:
        content_item = get_deprecated_htmlstory_config(context)
        msg = ("\nYou've configured your HTML story in the 'values' worksheet. "
                "Don't do this. It will work for now, but may stop working "
                "soon. Instead, configure it in the 'p2p_content_items' "
                "worksheet.")
        puts(colored.red(msg))
        p2p_publish_htmlstory(content_item, site, s3)

    except KeyError:
        # This is fine. Actually preferred. There shouldn't be anything
        # P2P-related in the
        pass

    try:
        content_items = context[CONTENT_ITEMS_WORKSHEET]
    except KeyError:
        # No worksheet with the P2P content item configuration.  Fail!
        msg = ("\nYou need a worksheet named {0} in your Tarbell spreadsheet "
               "to publish P2P content items").format(CONTENT_ITEMS_WORKSHEET)
        puts(colored.red(msg))
        return

    for i, content_item in enumerate(content_items):
        try:
            content_type = content_item['content_type']
        except KeyError:
            msg = ("\nYou need to specify a content type for P2P content "
                    "item {0}").format(i)
            continue

        try:
            if content_type == 'blurb':
                p2p_publish_blurb(content_item, site, s3)

            elif content_type == 'htmlstory':
                p2p_publish_htmlstory(content_item, site, s3)

            else:
                msg = ("\nUnknown content type '{0}' for P2P content "
                       "item {1}. Skipping publication.").format(content_type, i)
                puts(colored.yellow(msg))
                continue

        except MissingP2PContentItemFieldError as e:
            # The spreadsheet is missing a field needed to publish. Fail
            # gracefully.
            msg = ("\nYou need to specify field '{0}' for P2P content "
                    "item {1}. Skipping publication.").format(e.field_name, i)
            puts(colored.yellow(msg))
            continue

        except TemplateNotFound:
            msg = ("\nCould not find template '{0}' for P2P content "
                   "item {1}. Skipping publication").format(
                       content_item['template'], i)
            puts(colored.yellow(msg))
            continue


@register_hook('publish')
def p2p_publish(site, s3):
    try:
        p2p_publish_hook = site.project.P2P_PUBLISH_HOOK
    except AttributeError:
        p2p_publish_hook = p2p_publish_content_items

    p2p_publish_hook(site, s3)
