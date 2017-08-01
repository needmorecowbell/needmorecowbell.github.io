---
layout: post
title: Linux Tips: Easy Aliases
subtitle: "Make your computer feel like home"
author:     "Adam Musciano"
header-img: "img/post-bg-02.jpg"
---


#What is an Alias?

An alias is a global variable set by linux that can be freely called in terminals and scripts once defined. For example, if a user enters:
  ```
  alias weather='curl wttr.in/cancun' 

  ``` 
there will now be an alias called weather in that session which calls a service to get the weather in cancun. One think to be careful with when defining an alias is the whitespace -- an alias definition must be called as: 
  '''
  alias <aliasname>='<text-to-store>'
  '''  

If you've tried this, you might find that once you exited your session, the aliases were gone the next time you came back.So, how do you get around this? 

#Messing with the Configs

The most common way to make aliases persistent between sessions is to define them in the config file of your terminal. I personally use zsh, so my config file is named .zshrc in the root folder. This file runs absolutely anytime I open my terminal or call zsh. Because it is the first thing to run when I open a terminal, it is the best place to define my aliases. You can either append them directly into the file, or have all your aliases contained in a file that you run in the config.

To make it a little clear, I'll explain what it might look like. First, I got to my root directory and create a file called .aliases.sh.
   '''
 echo "" >> ~/.aliases.sh
   '''
Then I'll append an alias into the file with my favorite text editor. I will add the weather alias we went over at the begginning. With the alias file preloaded with code that is ready to be executed, it is time to call it in the terminal config file. So, I go into my .zshrc file, and append ''' source ~/.aliases.sh ''' to the end of the file. Save the file, and great! Now you have all your aliases neatly placed in one file that can be added to whenever you want. 

#Useful Aliases
 
Here is a list of some of my aliases that might be useful to you:
'''
# reboot / halt / poweroff
alias reboot='sudo /sbin/reboot'
alias shutdown='sudo /sbin/shutdown -t now'

#volume controls
alias volset='amixer sset Master '
alias volup='amixer sset Master 5%+'
alias voldown='amixer sset Master 5%-'

alias volmute='amixer -D pulse sset Master mute'
alias volmute='amixer -D pulse sset Master unmute'

#weather
alias weather="curl wttr.in/cancun"

# update on one command
alias update='sudo apt-get update && sudo apt-get upgrade'

#internet speeds
alias speedtest='curl -s  https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python -'

'''

#A Brief Warning

While aliases can save a lot of time, they can also be used exessively. If you find yourself having trouble working on other systems that don't have your aliases defined, you might be using too many. While it is simple to copy your alias file over to other computers (especially if you host your dotfiles with github), there may be times where they just aren't available to you. Use aliases responsibly, folks.
