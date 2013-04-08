#!/usr/bin/env ruby
##### inspired by:
## http://code.dimilow.com/git-subtree-notes-and-workflows/

puts PROJECTS = %w(
https://github.com/DerekV/pyramid-tutorial.git
https://github.com/dnouri/pyramid-tutorial.git
https://github.com/iElectric/almir.git
https://github.com/jmatthias/pyramid_apitree.git
https://github.com/karlproject/karl.git
https://github.com/Kotti/Kotti.git
https://github.com/Pylons/pyramid.git
https://github.com/Pylons/pyramid_chameleon.git
https://github.com/Pylons/pyramid_cookbook
https://github.com/Pylons/pyramid_rpc.git
https://github.com/Pylons/pyramid_tutorials.git
https://github.com/Pylons/shootout.git
https://github.com/Pylons/substanced.git
https://github.com/williamsb/Pyramid.git
).sort_by{|x| x.downcase}


def remote_name(git_url)
  "remote_#{git_url.split("/").last[0..-5]}"
end

def name(git_url)
  owner = (git_url.split("/")[-2])
  repo = git_url.split("/").last[0..-5]
  owner, repo = [owner, repo].map{|x| x.downcase}
  "#{owner}__#{repo}"
end

def add_remote(git_url)
  cmd = "git remote add #{remote_name(git_url)} #{git_url}"
  execute(cmd)
end

def add_project(git_url)
  cmd =  "git subtree add --prefix=#{name(git_url)} --squash #{git_url} master"
  execute(cmd)
end

def update_project(git_url)
  cmd = "git subtree pull --prefix #{name(git_url)} --squash #{git_url} master"
  execute(cmd)
end

def handle_project(git_url)
  if File.exist?(name(git_url))
    update_project(git_url)
  else
    add_remote(git_url)
    add_project(git_url)
  end
end

def execute(cmd)
  `#{cmd}`
  # puts cmd
end

### update projects
PROJECTS.each do |p| handle_project(p) end