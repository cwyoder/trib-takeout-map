# -*- coding: utf-8 -*-
from unittest import TestCase

from jinja2 import Template

try:
    from unittest import mock
except ImportError:
    # Python 2.7
    import mock

from blueprint import _get_published_content    


class BlueprintUtilsTestCase(TestCase):
    def test_get_published_content_curly_quotes(self):
        utf8_text = u"""
Novartis, which said it created and still manufactures metoprolol, did not
address questions about the findings. “Systemic safety risk assessment is
performed for all Novartis compounds on an annual basis,” the company said in a
written statement. “Novartis is committed to continue following industry
practice of assessing the risk of its drugs ... and to share collected data with
health authorities throughout the world on an ongoing basis.” According to IMS
Health data, the 2014 sales leader for metoprolol was AstraZeneca, which
declined to comment on the study. “We can confirm,” the company said, “that
AstraZeneca performed testing for QT prolongation during drug development as
defined by the regulatory requirements and our safety databases showed no signal
of QT prolongation attributed to metoprolol alone or concomitantly” with
fosphenytoin. Pfizer, the 2014 sales leader for fosphenytoin, said it was
unaware of any data for the drug that signals concerns regarding QT intervals.
“Ensuring the safety of patients and the appropriate use of our medicines is of
paramount concern to Pfizer,” the company said. “It is for this reason that we
continually monitor the safety and efficacy of our products to ensure the
benefit and risks are accurately described in our label. We work closely with
FDA and regulatory bodies across the globe, to ensure that all product labels
include the most up to date medical information.”
        """
        mock_template = Template('{{ text }}')
        mock_context = {
            'text': utf8_text
        }

        # Mock parts of the API for tarbell.app.TarbellSite 
        mock_site = mock.Mock()
        mock_site.app = mock.Mock()
        mock_site.app.jinja_env = mock.Mock()
        mock_site.app.jinja_env.get_template = mock.Mock(return_value=mock_template)
        mock_site.get_context = mock.Mock(return_value=mock_context)

        # Mock the S3 API.  We don't have to be very sophisticated here because
        # S3 doesn't get touched by this method because we're using this for
        # publishing to P2P
        mock_s3 = mock.Mock()

        output = _get_published_content(mock_site, mock_s3)
        self.assertTrue(u'“' not in output)
        self.assertTrue(u'”' not in output)
