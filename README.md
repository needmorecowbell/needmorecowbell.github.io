#Jekyll Server

##common server commands
```
jekyll build (compiles program)
jekyll serve --host $IP --port $PORT --baseurl ''  (runs server on c9)
jekyll serve (runs server)

```

#Jekyll-Compose

##commands
```
draft      # Creates a new draft post with the given NAME
post       # Creates a new post with the given NAME
publish    # Moves a draft into the _posts directory and sets the date
unpublish  # Moves a post back into the _drafts directory
page       # Creates a new page with the given NAME
```

##Common usage
```
bundle exec jekyll page "My New Page"
bundle exec jekyll post "My New Post"
bundle exec jekyll draft "My new draft"

bundle exec jekyll publish _drafts/my-new-draft.md
# or specify a specific date on which to publish it
bundle exec jekyll publish _drafts/my-new-draft.md --date 2014-01-24
bundle exec jekyll unpublish _posts/2014-01-24-my-new-draft.md
```



#Clean Blog by Start Bootstrap - Jekyll Version

The official Jekyll version of the Clean Blog theme by [Start Bootstrap](http://startbootstrap.com/).

###[View Live Demo &rarr;](http://blackrockdigital.github.io/startbootstrap-clean-blog-jekyll/)

## Before You Begin

In the _config.yml file, the base URL is set to /startbootstrap-clean-blog-jekyll which is this themes gh-pages preview. It's recommended that you remove the base URL before working with this theme locally!

It should look like this:
`baseurl: ""`

## What's Included

A full Jekyll environment is included with this theme. If you have Jekyll installed, simply run `jekyll serve` in your command line and preview the build in your browser. You can use `jekyll serve --watch` to watch for changes in the source files as well.

A Grunt environment is also included. There are a number of tasks it performs like minification of the JavaScript, compiling of the LESS files, adding banners to apply the MIT license, and watching for changes. Run the grunt default task by entering `grunt` into your command line which will build the files. You can use `grunt watch` if you are working on the JavaScript or the LESS.

You can run `jekyll serve --watch` and `grunt watch` at the same time to watch for changes and then build them all at once.

## Support

Visit Clean Blog's template overview page on Start Bootstrap at http://startbootstrap.com/template-overviews/clean-blog/ and leave a comment, email feedback@startbootstrap.com, or open an issue here on GitHub for support.
