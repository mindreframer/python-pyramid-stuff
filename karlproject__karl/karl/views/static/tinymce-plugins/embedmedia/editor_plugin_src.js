/*jslint undef: true, newcap: true, nomen: false, white: true, regexp: true */
/*jslint plusplus: false, bitwise: true, maxerr: 50, maxlen: 110, indent: 4 */
/*jslint sub: true */
/*globals window navigator document setTimeout tinymce alert $ */
/*globals KalturaConfiguration KalturaClient KalturaSessionService */
/*globals KalturaSessionType SWFObject */


/**
 * $Id: editor_plugin_src.js 1037 2009-03-02 16:41:15Z spocke $
 *
 * @author Moxiecode
 * @copyright Copyright � 2004-2008, Moxiecode Systems AB, All rights reserved.
 */

(function () {
    var each = tinymce.each;

    tinymce.create('tinymce.plugins.EmbedMediaPlugin', {
        init : function (ed, url) {
            var t = this;
            t.editor = ed;
            t.url = url;

            function isMedia(n) {
                return (/^mceItemFlash$/).test(n.className);
            }

            // Register commands
            ed.addCommand('mceEmbedMedia', function () {
                ed.windowManager.open({
                    file : url + '/media.htm',
                    width : 480 + parseInt(ed.getLang('embedmedia.delta_width', 0), 10),
                    height : 500 + parseInt(ed.getLang('embedmedia.delta_height', 0), 10),
                    inline : 1
                }, {
                    plugin_url : url
                });
            });

            // Register buttons
            ed.addButton('embedmedia', {title : 'media.desc', cmd : 'mceEmbedMedia'});

            ed.onNodeChange.add(function (ed, cm, n) {
                cm.setActive('embedmedia', n.nodeName == 'IMG' && isMedia(n));
            });

            ed.onInit.add(function () {

                if (ed.settings.content_css !== false) {
                    ed.dom.loadCSS(url + "/css/content.css");
                                }
                              
                if (ed && ed.plugins.contextmenu) {
                    ed.plugins.contextmenu.onContextMenu.add(function (th, m, e) {
                        if (e.nodeName == 'IMG' && /mceItemFlash/.test(e.className)) {
                            m.add({title : 'media.edit', icon : 'media', cmd : 'mceEmbedMedia'});
                        }
                    });
                }
            });

            ed.onBeforeSetContent.add(function (ed, o) {
                var snippet = t.newEmbedSnippet();
                var html = o.content;
                var shtml = snippet._objectsToSpans(html);
                o.content = shtml;
            }, t);

            ed.onSetContent.add(function () {
                var content = $(ed.getBody());

                content.find('span.mceItemEmbed,span.mceItemObject').each(function () {
                    var embed = $(this);
                    // If we are an embed inside an object, do not process
                    if (embed.is('span.mceItemEmbed') && 
                            embed.parent().is('span.mceItemObject')) {
                        return;
                    }
                    // Do the transformation

                    var snippet = t.newEmbedSnippet();
                    var embed_shtml;
                    if ($.browser.msie) {
                        embed_shtml = embed[0].outerHTML;
                    } else {
                        var wrapper = $('<div />');
                        wrapper.append(embed.clone());
                        embed_shtml = wrapper[0].innerHTML;
                        wrapper.remove();
                    }
                    var embed_text = snippet._spansToObjects(embed_shtml);

                    var result = $('<img />')
                        .attr('src', t.url + '/img/trans.gif')
                        .addClass('mceItemFlash')
                        .addClass('mceMarker-embedmedia')
                        .attr('title', embed_text)
                        .attr('width', embed.attr('width') || null)
                        .attr('height', embed.attr('height') || null);
                        //.attr('align', f.align.options[f.align.selectedIndex].value);
                    // XXX for some reason, this serialization is essential on IE
                    result = $('<div />').append(result).html();
                    embed.replaceWith(result);
                });
                content.find('span.mceEndObject').remove();

            });

            function getAttr(s, n) {
                n = new RegExp(n + '=\"([^\"]+)\"', 'g').exec(s);

                return n ? ed.dom.decode(n[1]) : '';
            }

            ed.onPostProcess.add(function (ed, o) {
                o.content = o.content.replace(/<img[^>]+>/g, function (img) {
                    var cl = getAttr(img, 'class');
                    // The class may have a leading space
                    cl = cl.replace(/^ */, '').replace(/ *$/, '');
                    // this class is never removed
                    if (cl == 'mceMarker-embedmedia') {
                        // update width, height
                        var snippet = t.newEmbedSnippet();
                        snippet.setContent(getAttr(img, 'title'));
                        snippet.setParms({
                            width: getAttr(img, 'width'),
                            height: getAttr(img, 'height')
                        });
                        img = snippet.getContent();
                        snippet.wrapper.remove();
                    }
                    return img;
                });
            });

        },
            

        newEmbedSnippet : function () {
            // manipulation of embed snippets
            // created here because at this point we have jquery
            // for sure.

            var EmbedSnippet = function EmbedSnippet() {};
            $.extend(EmbedSnippet.prototype, {

                _objectsToSpans : function (str) {
                    str = str.replace(/<object([^>]*)>/gi, '<span class="mceItemObject"$1>');
                    str = str.replace(/<embed([^>]*)\/?>/gi, '<span class="mceItemEmbed"$1></span>');
                    str = str.replace(/<embed([^>]*)>/gi, '<span class="mceItemEmbed"$1>');
                    str = str.replace(/<\/(object)([^>]*)>/gi, '<span class="mceEndObject"></span></span>');
                    str = str.replace(/<\/embed>/gi, '');
                    str = str.replace(/<param([^>]*)\/?>/gi, '<span class="mceItemParam"$1></span>');
                    str = str.replace(/<\/param>/gi, '');
                    return str;
                },

                _spansToObjects : function (str) {
                    str = str.replace(/<span([^>]*) class="?mceItemParam"?([^>]*)><\/span>/gi, '<param$1 $2></param>');
                    str = str.replace(/<span([^>]*) class="?mceItemEmbed"?([^>]*)><\/span>/gi, '<embed$1 $2></embed>');
                    str = str.replace(/<span([^>]*) class="?mceItemObject"?([^>]*)>/gi, '<object$1 $2>');
                    str = str.replace(/<span class="?mceEndObject"?><\/span><\/span>/gi, '</object>');
                    return str;
                },

                setContent: function (html) {
                    this.wrapper = $('<div />');
                    var wrapper = this.wrapper;
                    var shtml = this._objectsToSpans(html);
                    wrapper[0].innerHTML = shtml;

                    this.root = wrapper.children();
                    var root = this.root;
                    // detect type
                    this.emtype = null;
                    // wmode = opaque workaround
                    var wmode_key = 'wmode';
                    var wmode_value = 'opaque';
                    //
                    if (root.is('span.mceItemObject')) {
                        var inside = root.find('span.mceItemEmbed');
                        if (inside) {
                            this.emtype = 'object+embed';
                            this.inside = inside;
                            // remove bad attributes. (Important: 
                            // will explode flash if left in)
                            if (inside.attr('mce_src')) {
                                inside.removeAttr('mce_src');
                            }
                            // wmode = opaque workaround,
                            // also add to embed
                            inside.attr(wmode_key, wmode_value);
                        }

                        // Fix missing params (broken in IE8, kaltura)
                        var params = ['allowScriptAccess', 'allowNetworking', 'allowFullScreen',
                            'bgcolor', 'movie', 'flashVars'];
                        var to_add = [];
                        $.each(params, function (i, value) {
                            var found = false;
                            root.find('span.mceItemParam').each(function (i, elem) {
                                var a = $(elem).attr('name');
                                if (a == value || a == value.toLowerCase()) {
                                    found = true;
                                    return false;
                                }
                            });
                            if (! found) {
                                // Is there an attr?
                                if (root.attr(value)) {
                                    to_add.push({k: value, v: root.attr(value)});
                                } else if (root.attr(value.toLowerCase())) {
                                    to_add.push({k: value, v: root.attr(value.toLowerCase())});
                                } else if (value == 'movie') {
                                    // special handling of resource
                                    if (root.attr('resource')) {
                                        to_add.push({k: value, v: root.attr('resource')});
                                    }
                                }
                            }
                        });
                        $.each(to_add, function (i, value) {
                            try {
                                $('<span class="mceItemParam"></span>')
                                    .attr('name', value.k)
                                    .attr('value', value.v)
                                    .prependTo(root);
                            } catch (e) {}
                        });

                        // Workaround broken z-index implemention in IE6, IE7
                        // add wmode = opaque both as param. and as an attribute
                        // of the object tag.
                        // If it already exists, we overwrite them
                        var found = false;
                        root.find('span.mceItemParam').each(function (i, elem) {
                            var a = $(elem).attr('name');
                            if (a == wmode_key) {
                                found = true;
                                $(elem).attr('value', wmode_value);
                                return false;
                            }
                        });
                        if (! found) {
                            try {
                                $('<span class="mceItemParam"></span>')
                                    .attr('name', wmode_key)
                                    .attr('value', wmode_value)
                                    .prependTo(root);
                            } catch (e) {}
                        }
                        root.attr(wmode_key, wmode_value);

                    }

                    // remove bad attributes. (Important: 
                    // will explode flash if left in)
                    if (root.attr('mce_src')) {
                        root.removeAttr('mce_src');
                    }
                    // cascade
                    return this;
                },

                getContent: function () {
                    var shtml = this.wrapper.html();
                    var html = this._spansToObjects(shtml);
                    return html;
                },

                getParms: function () {
                    return {
                        width: this.root.attr('width'),
                        height: this.root.attr('height')
                    };
                },

                setParms: function (parms) {
                    if (this.emtype == 'object+embed') {
                        if (parms.width) {
                            this.root.attr('width', parms.width); 
                            this.inside.attr('width', parms.width); 
                        }
                        if (parms.height) {
                            this.root.attr('height', parms.height); 
                            this.inside.attr('height', parms.height); 
                        }
                    } else {
                        if (parms.width) {
                            this.root.attr('width', parms.width); 
                        }
                        if (parms.height) {
                            this.root.attr('height', parms.height); 
                        }
                    }
                    return this;
                }

            });
            // give access to the class from the popup
            this.newEmbedSnippet = function newEmbedSnippet() {
                return new EmbedSnippet();   
            };
            return this.newEmbedSnippet();
        },

        getJQuery: function () {
            return window.jQuery;
        },

        getInfo : function () {
            return {
                longname : 'Media',
                author : 'Moxiecode Systems AB',
                authorurl : 'http://tinymce.moxiecode.com',
                infourl : 'http://wiki.moxiecode.com/index.php/TinyMCE:Plugins/media',
                version : tinymce.majorVersion + "." + tinymce.minorVersion
            };
        }

    });

    // Register plugin
    tinymce.PluginManager.add('embedmedia', tinymce.plugins.EmbedMediaPlugin);
})();
