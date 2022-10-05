---
layout: post
title: Clear Your Terminal in Style
headerimg: "/img/post-bg-09.png"
date: "2020-03-04"
---



If you're someone like me who habitually clears their terminal, sometimes you want a little excitement in your life. Here is a way to do just that.

## Percent Chance for command to run

This post revolves around the idea of giving a command a percent chance of running. While the topic at hand is not serious, this simple technique has potential in your scripts.

```bash
[ $[$RANDOM % 10] = 0 ] && do_this || do_that
```

This gives roughly a 1 in 10 chance of do_this running, and a 9 in 10 chance of do_that running. You can omit `|| do_that` to just have a 10 percent chance of `do_this` running.

Like Russian roulette?

 ```bash 
 [ $[$RANDOM % 6] = 0 ] && sudo rm -rf / || echo "Not today"
 ```


## Cbeams

Jonathan Hartley (tartley on GitHub), creater of the popular colorama python module, also made a cool little terminal application tool called cbeams. We can use his animation with a little bit of bash goodness to clear our terminal.


```bash
pip install cbeams
```

This is the animation command, which overwrites the current text on the terminal:

```bash
cbeams -o
```

To attach it to clear, we extend the command's functionality:

```bash
alias clear='[ $[$RANDOM % 10] = 0 ] && timeout 6 cbeams -o; clear || clear'
```

This way, there is a 10% chance of the cbeams command running. When it runs, it will look like this:

<p align="center">
    <img src="https://user-images.githubusercontent.com/7833164/75482303-8a521380-5972-11ea-9415-b87bd7eef5ba.gif">
</p>

## SL

The SL command stands for steam locomotive. It came about because of how often people mistype ls. Instead of this use, how nice would it be if a train ran the error logs you're getting off the screen!

```bash
sudo apt install sl
```

```bash
alias clear='[ $[$RANDOM % 10] = 0 ] && sl; clear || clear'
```

<p align="center">
    <img src="https://user-images.githubusercontent.com/7833164/75565460-f9377700-5a1b-11ea-9b16-9f8974413a84.gif">
</p>



## Cmatrix

The cmatrix command is based off the [digital rain](https://en.wikipedia.org/wiki/Matrix_digital_rain) animation from the opening scenes of Matrix movie series.

```bash
sudo apt install cmatrix
```

```bash
alias clear='[ $[$RANDOM % 10] = 0 ] && timeout 3 cmatrix; clear || clear'
```

<p align="center">
    <img src="https://user-images.githubusercontent.com/7833164/75938216-2d17ff80-5e55-11ea-9df9-be5f097f0523.gif">
</p>

## Extra: VT100 Files

Here's a piece of internet history. [VT100](https://en.wikipedia.org/wiki/VT100) is a video terminal made in 1978. There are archives of animations made with this tool -- some dating back more than 40 years ago. They are a lot of fun to look back on. I can't imagine how much time it took to make some of these. Take a look at a large archive from [here](http://artscene.textfiles.com/vt100/). They also provide a perl script which allows you to view the files at the speed they were meant to be seen, [here](http://artscene.textfiles.com/viewers/linux/slowcat.pl).

Here is a recording of a twilight zone animation I found particularly impressive:


<p align="center">
  <video width="700" height="500" controls muted>
    <source src="https://s3cdn.617a.net/amblog/assets/videos/twilightzone.mp4" type="video/mp4">
    Your browser does not support the video tag.
  </video> 
</p>

