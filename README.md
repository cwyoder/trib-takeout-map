# 100 best takeout spots in Chicago


A [Tarbell](http://tarbell.io) project that publishes to a P2P HTML Story. This is branch master.


Assumptions
-----------

* Python 2.7
* Tarbell 1.0.\*
* Node.js
* grunt-cli (See http://gruntjs.com/getting-started#installing-the-cli)

Custom configuration
--------------------

You should define the following keys in either the `values` worksheet of the Tarbell spreadsheet or the `DEFAULT_CONTEXT` setting in your `tarbell_config.py`:

* p2p\_slug
* headline 
* seotitle
* seodescription
* keywords
* byline

Note that these will clobber any values set in P2P each time the project is republished.  

Building front-end assets
-------------------------

This blueprint creates configuration to use [Grunt](http://gruntjs.com/) to build front-end assets.

When you create a new Tarbell project using this blueprint with `tarbell newproject`, you will be prompted about whether you want to use [Sass](http://sass-lang.com/) to generate CSS and whether you want to use  [Browserify](http://browserify.org/) to bundle JavaScript from multiple files.  Based on your input, the blueprint will generate a `package.json` and `Gruntfile.js` with the appropriate configuration.

After creating the project, run:

    npm install

to install the build dependencies for our front-end assets.

When you run:

    grunt

Grunt will compile `sass/styles.scss` into `css/styles.css` and bundle/minify `js/src/app.js` into `js/app.min.js`.

If you want to recompile as you develop, run:

    grunt && grunt watch

This blueprint simply sets up the the build tools to generate `styles.css` and `js/app.min.js`, you'll have to explicitly update your templates to point to these generated files.  The reason for this is to make you think about whether you're actually going to use an external CSS or JavaScript file and avoid a request for an empty file if you don't end up putting anything in your custom stylesheet or JavaScript file.

To add `app.min.js` to your template file:

    
    <script src="js/app.min.js"></script>
    

# How to use the blurb files

We can insert elements into stories using HTML code blocks in Ellipsis. We do this through iframes. This lets us have our elements on an S3 server, outside of Ellipsis. This makes it easier to push/pull changes using Git, and allows us to keep a code repository outside of Ellipsis. 

We are going to use Pym.js, a JavaScript library developed by NPR that allows the parent and child page to talk to each other. It redraws the iframe on the parent to fit the content of the child. Here is the Pym.js documentation: http://blog.apps.npr.org/pym.js/

NOTE ON STYLES: For now you need to uncomment `@import 'trib-typography'` in your sass file if you want the basic p tags to be styled to look like arc. 


## Using one blurb on a page 

Use the `blurb.html` file to design and develop your blurb, renaming it to somethign that makes sense. Design and develop the page as you normally would. You can use all the normal SASS, JavaScript and Jinja you want. Since this all lives in S3 we don’t need to worry about it interacting poorly with Ellipsis. 

After you’re done publish the blurb using `tarbell publish production`. Note that the blurb will not work if published to staging, even if you’re just previewing the graphic in Ellipsis. This is because our staging server is not https, and Ellipsis will block it.

You’ll need to fill out the first line of the `p2p_content_items` with dummy text, minus the p2p thumbnail. This is due to an old publishing bug that was never fixed. If there isn’t a thumbnail, nothing will actually go to p2p. It will go to S3, though. 

Now that the blurb is published, you can send the embed code to the web team. Here’s the code to make that happen:

`<style> .ai2html-blurb iframe {min-width:100%; width:280px;}</style>
<div class='ai2html-blurb' id="blurb-gfx"></div>
<script src="https://pym.nprapps.org/pym.v1.min.js"></script>
<script>
    var pymParent = new pym.Parent('blurb-gfx', 'https://graphics.chicagotribune.com/SLUG/PATH', {});
</script>`

Replace the `GRAPHIC-ID` with an id that makes sense. It needs to go on both the div and the pym.Parent function. Replace the URL with the correct url of the final graphic. Send this block of code to the member of the audience team that is producing the story.


## More than one blurb on a page

Duplicate your `blurb.html file` and name it something different from your first blurb. You'll need as many code snippets as you have blurbs to give to the web producer. You only need to include the Pym.js CDN one time, with the first include.

Here is what the first include would be:

`<style> .ai2html-blurb iframe {min-width:100%; width:280px;}</style>
<div class='ai2html-blurb' id="blurb-gfx"></div>
<script src="https://pym.nprapps.org/pym.v1.min.js"></script>
<script>
    var pymParent = new pym.Parent('blurb-gfx', 'https://graphics.chicagotribune.com/SLUG/PATH', {});
</script>`

And here is what each additional include would look like:

`<style> .ai2html-blurb iframe {min-width:100%; width:280px;}</style>
<div class='ai2html-blurb' id="blurb-gfx"></div>
<script>
    var pymParent = new pym.Parent('blurb-gfx', 'https://graphics.chicagotribune.com/SLUG/PATH', {});
</script>`    
    