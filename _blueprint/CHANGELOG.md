Changelog
=========

2016-06-22
----------

Update the version of `python-tribune-viztools` to 0.4.0 which adds these things:

* Support ES6 in application JavaScript using Babel
* Use node-sass instead of Ruby sass
* Create vendor JavaScript bundles
* Use minifyify directly as Browserify plugin instead of using grunt-minifyify
* Always use Browserify and Sass instead of giving user the choice.  See [#1096](https://tribune.unfuddle.com/a#/projects/6/tickets/by_number/1096).
* Invoke JavaScript/CSS build with `npm run build` and `npm run watch` instead of `grunt` and `grunt watch`. See [#1099](https://tribune.unfuddle.com/a#/projects/6/tickets/by_number/1099).
