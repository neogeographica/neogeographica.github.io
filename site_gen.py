import Elements, postmarkup
import argparse, sys, os, re, shutil, contextlib, subprocess, tempfile

# Paths are relative to the home dir of this script.
this_dir = sys.path[0]

# Identify the root directories for the source site content and the location
# to place the generated/processed site content.
guides_src_dir = os.path.join(this_dir, 'guides_bbcode')
guides_dest_dir = os.path.join(this_dir, 'guides_html')
src_dir = os.path.join(this_dir, 'site_src')
dest_subdir = 'site'
dest_dir = os.path.join(this_dir, dest_subdir)
guides_ref_file = os.path.join(src_dir, 'pages', 'guides',
                               '`guide_sections_dir.txt')

# Flags to control whether we run stuff through YUI Compressor. Not currently
# exposed as command-line args... note that if only processing HTML pages, this
# is basically representing whether the last processing of CSS/JS was minimized.
minimize_css = True
minimize_js = True

# Identify the YUI jarfile to use.
yui_jar = 'yuicompressor-2.4.8.jar'
min_cmd_prefix = ['java', '-jar', os.path.join(this_dir, yui_jar)]

# To avoid confusion, the filenames for minimized scripts will have ".min"
# inserted before the final extension (".css" or ".js"). That means that any
# internal references to those filenames will need to be fixed up. Below are
# definitions for the necessary regex work.
css_import_pattern = re.compile('@import url\(([^h][^\)]*)\.css\)')
css_min_import_fun = lambda match: ''.join(['@import url(', match.group(1),
                                            '.min.css)'])
css_href_pattern = re.compile('href="([^h][^"]*/[^/"]*)\.css"')
css_min_href_fun = lambda match: ''.join(['href="', match.group(1), '.min.css"'])
js_src_pattern = re.compile('src="([^h][^"]*/[^/"]*)\.js"')
js_min_src_fun = lambda match: ''.join(['src="', match.group(1), '.min.js"'])

# Replacements for contents of links to Steam Guides.
link_xlate = {
    'http://steamcommunity.com/sharedfiles/filedetails/?id=113166739' :
    (None, 'Ultimate Quake Patch'),
    'http://steamcommunity.com/sharedfiles/filedetails/?id=113399618' :
    (None, 'How to fix CD audio looping on Windows Vista/7'),
    'http://steamcommunity.com/sharedfiles/filedetails/?id=118401000' :
    ('engines.html', 'Quake Engines, Old and New'),
    'http://steamcommunity.com/sharedfiles/filedetails/?id=287224659' :
    ('troubleshooting.html', 'Troubleshooting'),
    'http://steamcommunity.com/sharedfiles/filedetails/?id=119489135' :
    ('soundtrack_solutions.html', 'Quake Soundtrack Solutions'),
    'http://steamcommunity.com/sharedfiles/filedetails/?id=120426294' :
    ('owners_manual.html', 'Quake Owner\'s Manual'),
    'http://steamcommunity.com/sharedfiles/filedetails/?id=123626484' :
    ('deathmatch_with_bots.html', 'Deathmatch With Bots (on hundreds of maps)'),
    'http://steamcommunity.com/sharedfiles/filedetails/?id=166554615' :
    (None, 'Custom Singleplayer Levels')
}

# Form the div that holds a popup image.
def popup_div_img(div_id, img_name):
    return (u'<div class="jqmWindow" id="%s">'
             '[local_image(\'%s\', \'jqmClose jqmWindowContent\')]</div>' %
            (div_id, img_name))

def popup_div_sshot(div_id, img_url):
    return (u'<div class="jqmWindow" id="%s">'
             '<img src="%s" class="jqmClose jqmWindowContent"></img></div>' %
            (div_id, img_url))

# Var to hold those divs as we build them.
popup_divs_header = '<!-- begin: image popups -->'
popup_divs_footer = '<!-- end: image popups -->'
popup_divs = popup_divs_header

# How to convert Valve's special-snowflake previewimg tag to HTML.
class PreviewImgTag(postmarkup.TagBase):
    def __init__(self, name, **kwargs):
        super(PreviewImgTag, self).__init__(name, inline=True)
    def render_open(self, parser, node_index):
        global popup_divs
        self.skip_contents(parser)
        [img_id, img_props_list, img_name] = self.params.split(';')
        img_props = 'guidePic ' + img_props_list.replace(',', ' ')
        if img_props_list.find('sizeOriginal') == -1:
            popup_divs = '\n'.join([popup_divs, popup_div_img(img_id, img_name)])
        return (u'[local_id_image(\'%s\',\'trigger-%s\',\'%s\')]' %
                (img_name, img_id, img_props))

# How to handle screenshot tag.
class ScreenshotTag(postmarkup.TagBase):
    def __init__(self, name, **kwargs):
        super(ScreenshotTag, self).__init__(name, inline=True)
    def render_open(self, parser, node_index):
        global popup_divs
        self.skip_contents(parser)
        [img_id, img_props_list, img_name] = self.params.split(';')
        img_id = 's' + img_id
        img_url = 'http://' + img_name
        img_props = 'guidePic ' + img_props_list.replace(',', ' ')
        if img_props_list.find('sizeOriginal') == -1:
            popup_divs = '\n'.join([popup_divs, popup_div_sshot(img_id, img_url)])
        return (u'<img src="%s" id="trigger-%s" class="%s"></img>' %
                (img_url, img_id, img_props))

# How to handle embedded YouTube vidoe.
class PreviewYouTubeTag(postmarkup.TagBase):
    def __init__(self, name, **kwargs):
        super(PreviewYouTubeTag, self).__init__(name, inline=True)
    def render_open(self, parser, node_index):
        self.skip_contents(parser)
        [video_id, video_props_list] = self.params.split(';')
        video_props = 'guideWidescreenVid ' + video_props_list.replace(',', ' ')
        return (u'[controls_video(\'%s\',\'%s\')]' % (video_id, video_props))

# How to stick a bullet point in front of an element's content.
class BulletedTag(postmarkup.SimpleTag):
    def render_open(self, parser, node_index):
        tag = super(BulletedTag, self).render_open(parser, node_index)
        return tag + u'&bull; '

# Intercept links to other Steam guides
class GuideInterceptLinkTag(postmarkup.LinkTag):
    def render_open(self, parser, node_index):
        tag = super(GuideInterceptLinkTag, self).render_open(parser, node_index)
        contents = self.get_contents(parser)
        if contents in link_xlate:
            self.skip_contents(parser)
            (new_link, link_name) = link_xlate[contents]
            if new_link is None:
                img_file = 'steam.png'
            else:
                img_file = 'neo.png'
                tag = tag.replace(contents, new_link)
            img = ('<img src="[local_common_images_path()]%s" '
                   'class="linkBadge"></img>') % img_file
            return ''.join([tag, img, ' ', link_name,
                            self.render_close(parser, node_index), '<br/>'])
        if contents.find('steamcommunity.com') != -1:
            print 'Warning: untranslated steamcommunity.com link: %s' % contents
        return tag

# Simple table tags
class TableBaseTag(postmarkup.TagBase):
    def __init__(self, name, html_name, **kwargs):
        super(TableBaseTag, self).__init__(name, strip_first_newline=True)
        self.html_name = html_name
    def render_open(self, parser, node_index):
        return u'<%s>' % self.html_name
    def render_close(self, parser, node_index):
        return u'</%s>' % self.html_name
class TableTag(TableBaseTag):
    def __init__(self, name, **kwargs):
        super(TableTag, self).__init__(name, 'table')
class TableHeaderTag(TableBaseTag):
    def __init__(self, name, **kwargs):
        super(TableHeaderTag, self).__init__(name, 'th')
class TableRowTag(TableBaseTag):
    def __init__(self, name, **kwargs):
        super(TableRowTag, self).__init__(name, 'tr')
class TableDataTag(TableBaseTag):
    def __init__(self, name, **kwargs):
        super(TableDataTag, self).__init__(name, 'td')


# Instantiate our BBCode converter.
bbc_converter = postmarkup.create(use_pygments=False, exclude=[u'url'])
bbc_converter.tag_factory.add_tag(PreviewImgTag, u'previewimg')
bbc_converter.tag_factory.add_tag(ScreenshotTag, u'screenshot')
bbc_converter.tag_factory.add_tag(PreviewYouTubeTag, u'previewyoutube')
bbc_converter.tag_factory.add_tag(BulletedTag, u'h1', u'h3')
bbc_converter.tag_factory.add_tag(GuideInterceptLinkTag, u'url',
                                  annotate_links=False)
bbc_converter.tag_factory.add_tag(TableTag, u'table')
bbc_converter.tag_factory.add_tag(TableHeaderTag, u'th')
bbc_converter.tag_factory.add_tag(TableRowTag, u'tr')
bbc_converter.tag_factory.add_tag(TableDataTag, u'td')

# Simple context manager to push and pop working directory.
@contextlib.contextmanager
def visit_dir(dir):
    cwd = os.getcwd()
    os.chdir(dir)
    try:
        yield
    finally:
        os.chdir(cwd)

# Run a directory tree's contents through Elements processing, completely
# replacing a destination directory tree.
def run_elements(src_dir, dest_dir, sub_dir):
    shutil.rmtree(os.path.join(dest_dir, sub_dir), ignore_errors=True)
    Elements.process(src_dir, dest_dir, sub_dir)

# File-transform function for minimizing CSS/JS.
def min_xform(in_path, file_name, dot_ext, out_dir):
    # Change the dest file extension.
    out_file_name = file_name[:-len(dot_ext)] + '.min' + dot_ext
    out_path = os.path.join(out_dir, out_file_name)
    # Add the input file to the minimize command line.
    cmd = list(min_cmd_prefix)
    cmd.extend([in_path])
    # Create the output file and write the output of the
    # minimize command to it.
    with open(out_path, 'w') as out_fd:
        subprocess.call(cmd, stdout=out_fd)

# File-transform function for converting BBCode to HTML.
def bbc_xform(in_path, file_name, dot_ext, out_dir):
    # Change the dest file extension.
    out_file_name = '%s %s.html' % (os.path.basename(out_dir),
                                    file_name[:-len(dot_ext)])
    out_path = os.path.join(out_dir, out_file_name)
    # Parse and convert.
    with open(in_path, 'r') as in_fd:
        bbc_in = in_fd.read()
    # Work around the dislike of empty table cells.
    # XXX If Valve BBCode accepts [sp] as nbsp, that could be another solution.
    final_bbc_in = bbc_in.replace('[td][/td]', '[td]_[/td]')
    html_out = bbc_converter(final_bbc_in, paragraphs=True)
    # Fix up some presentation issues that I don't think I can handle with
    # postmarkup options.
    final_html_out = html_out.replace(
        '<p><h3>', '<h3>').replace(
        '</h3><br/>', '</h3><p>').replace(
        '<td>_</td>', '<td>&nbsp;</td>').replace(
        '<br/><ul>', '</p><p><ul>')
    # And write the results.
    with open(out_path, 'w') as out_fd:
        out_fd.write(final_html_out)

# Handle the accumulated popup divs for a directory.
def bbc_record_popups(dir):
    global popup_divs
    popup_divs = '\n'.join([popup_divs, popup_divs_footer])
    file_name = '%s 00 popups.html' % os.path.basename(dir)
    file_path = os.path.join(dir, file_name)
    with open(file_path, 'w') as out_fd:
        out_fd.write(popup_divs)
    popup_divs = popup_divs_header

# Copy a directory tree's contents when they match the given file extension.
# Optionally apply a transformation to the file contents. Source and dest
# directories can usefully be the same if and only if there is a transformation
# ("in-place xform").
def copy_files(src_dir, dest_dir, sub_dir, file_ext, xform=None, dir_func=None):
    # Determine if this operation is "in-place".
    in_place = (src_dir == dest_dir)
    if in_place:
        if xform is None:
            # If in-place and not xforming, nothing to do.
            return
    else:
        # If not in-place, nuke the destination directory tree.
        dest_tree = os.path.join(dest_dir, sub_dir)
        if dest_tree.endswith("/."): # Make OS X happy with "." subdir.
            dest_tree = dest_tree[:-2]
        shutil.rmtree(dest_tree, ignore_errors=True)
    # Traverse the source directory tree.
    dot_ext = '.' + file_ext
    with visit_dir(src_dir):
        for dir_path, dir_names, file_names in os.walk(sub_dir):
            cur_src_dir = os.path.join(src_dir, dir_path)
            cur_dest_dir = os.path.join(dest_dir, dir_path)
            if not in_place:
                # If not in-place, make sure the dest directory exists.
                os.makedirs(cur_dest_dir)
            # Look at all the files in this directory.
            for f in file_names:
                # Process the ones with the right extension.
                if f.endswith(dot_ext):
                    in_path = os.path.join(cur_src_dir, f)
                    if xform is not None:
                        # Apply xform.
                        xform(in_path, f, dot_ext, cur_dest_dir)
                        # If in-place, remove the original file.
                        if in_place:
                            os.remove(in_path)
                    else:
                        # If not xforming, just copy the file.
                        out_path = os.path.join(cur_dest_dir, f)
                        shutil.copyfile(in_path, out_path)
            # Do any per-directory work
            if dir_func is not None:
                dir_func(cur_dest_dir)

# Replace each reference to a script filename with the "minimized" version of
# that filename.
def min_refs(dest_dir, sub_dir, file_ext, match_pattern, replace_fun):
    # Traverse the directory tree.
    dot_ext = '.' + file_ext
    root_dir = os.path.join(dest_dir, sub_dir)
    for dir_path, dir_names, file_names in os.walk(root_dir):
        # Look at all the files in this directory.
        for f in file_names:
            # Process the ones with the right extension.
            if f.endswith(dot_ext):
                in_path = os.path.join(dir_path, f)
                # Create a temporary file to write the new content.
                with tempfile.NamedTemporaryFile(delete=False) as out_fd:
                    # Remember the name of the temporary file.
                    out_path = out_fd.name
                    # Open the source file and process each line, modifying
                    # references to script file names as necessary. Write
                    # the results to the temporary file.
                    with open(in_path, 'r') as in_fd:
                        for line in in_fd:
                            new_line = match_pattern.sub(replace_fun, line)
                            out_fd.write(new_line)
                # Delete the source file and rename the temporary file to
                # replace it.
                os.remove(in_path)
                os.rename(out_path, in_path)


# OK, definitions done, away we go:

# Assume HTML-only unless told otherwise
parser = argparse.ArgumentParser()
parser.add_argument("--css", action="store_true")
parser.add_argument("--js", action="store_true")
parser.add_argument("--nohtml", action="store_true")
args = parser.parse_args()
css = args.css
js = args.js
html = not args.nohtml

if css:
    print("  processing CSS")
    # Do "Elements" processing on the CSS scripts.
    run_elements(src_dir, dest_dir, 'css')
    # Minimize the css scripts if desired.
    if minimize_css:
        copy_files(dest_dir, dest_dir, 'css', 'css', min_xform)
        min_refs(dest_dir, 'css', 'css', css_import_pattern, css_min_import_fun)
if js:
    print("  processing JS")
    # Copy the JS scripts to the destination location; minimize them if desired.
    xform = min_xform if minimize_js else None
    copy_files(src_dir, dest_dir, 'js', 'js', xform)
if html:
    print("  processing HTML")
    # Munge BBCode for guides.
    with open(guides_ref_file, 'w') as out_fd:
        out_fd.write('#dir: ' + guides_dest_dir)
    copy_files(guides_src_dir, guides_dest_dir, '.', 'txt', bbc_xform, bbc_record_popups)
    # Do "Elements" processing on the HTML pages.
    run_elements(src_dir, dest_dir, 'pages')
    # Modify the html pages to account for minimized CSS/JS scripts.
    if minimize_css:
        min_refs(dest_dir, 'pages', 'html', css_href_pattern, css_min_href_fun)
    if minimize_js:
        min_refs(dest_dir, 'pages', 'html', js_src_pattern, js_min_src_fun)
    # Copy munged index.html to top level.
    in_path = os.path.join(dest_dir, 'pages', 'index.html')
    with open(in_path, 'r') as in_fd:
        orig_index = in_fd.read()
    top_index = orig_index.replace('="../', '="%s/' % dest_subdir)
    with open('index.html', 'w') as out_fd:
        out_fd.write(top_index)
