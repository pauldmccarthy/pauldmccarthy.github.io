#!/usr/bin/env python
# /// script
# dependencies = [
#   "jinja2",
#   "pyyaml"
# ]
# ///

import             sys
import os.path  as op
import textwrap as tw

import jinja2  as j2
import            yaml


THISDIR = op.abspath(op.dirname(__file__))


def html():
    def url(href, title=None):
        if title is None:
            title = href
        return f'<a href="{href}">{title}</a>'

    def preproc(text, cls=None):
        # strip whitespace from each line
        if cls is None: para = '<p>'
        else:           para = f'<p class="{cls}">'
        text  = f'{para}{text.strip()}'
        lines = [l.strip() for l in text.split('\n')]
        text  = '\n'.join(lines)
        # double newline -> para
        return text.replace('\n\n', f'\n{para}')

    def bold(text):
        return f'<strong>{text}</strong>'

    def italic(text):
        return f'<em>{text}</em>'

    def code(text):
        return f'<code>{text}</code>'

    def project(content, tagline=None, icon=None, icon_url=None):

        if icon is None:
            return preproc(content, 'ma3')

        content = preproc(content)

        if icon_url is not None:
            icon = f'<a class="w-10 pa1" href="{icon_url}"><img src="{icon}"/></a>'
        else:
            icon = f'<img class="w-10 pa1" src="{icon}"/>'

        if tagline is not None:
            tagline = f'<br><span class="f7 silver i small-caps">{tagline}</span>'
        else:
            tagline = ''

        return '\n'.join([
            '<div class="flex items-center">',
            icon,
            '<div class="w-90 pa1">',
            f'<span>{content}</span>',
            tagline,
            '</div>',
            '</div>'])

    def pub(title, author, url, doi):
        return tw.dedent(f"""
        <p class="ma3">
        <span class="small-caps">{title}</span>
        <span class="f7 i silver">{author}
        <a href="{url}">{doi}</a>
        </span>
        </p>
        """)

    def section(title, subtitle, content, id=None, tagline=None, icon=None, icon_url=None):

        if id is not None: id = f' id="{id}" '
        else:              id = ''

        title    = f'<h2 {id} class="normal small-caps">{title}</h2>'
        subtitle = f'<h3 class="normal small-caps i silver">{subtitle}</h2>'
        content  = preproc(content)

        if tagline is not None:
            tagline = f'<span class="f7 silver i small-caps">{tagline}</span>'
        else:
            tagline = ''

        if icon is not None:
            if icon_url is not None:
                icon = f'<a class="w-20 pa1" href="{icon_url}"><img src="{icon}"/></a>'
            else:
                icon = f'<img class="w-20 pa1" src="{icon}"/>'

        if icon is None:
            return f'{title}\n{subtitle}\n{tagline}\n{content}\n'
        else:
            return tw.dedent(f"""
            {title}
            {subtitle}
            <div class="flex items-center">
            <div class="w-80 pa1">{content}</div>
            {icon}
            </div>
            """)

    templates = {
        'index.html'     : f'{THISDIR}/resources/index.html.template',
        'side_menu.html' : f'{THISDIR}/resources/side_menu.html.template',
    }

    return {}, {
        'templates'    : templates,
        'url_raw'      : url,
        'bold'         : bold,
        'b'            : bold,
        'italic'       : italic,
        'i'            : italic,
        'code'         : code,
        'c'            : code,
        'pub_raw'      : pub,
        'project_raw'  : project,
        'section'      : section,
    }


def latex():

    def code(text):
        return rf'\texttt{{{text}}}'

    def italic(text):
        return rf'\textit{{{text}}}'

    def bold(text):
        return rf'\textbf{{{text}}}'

    def url(href, title=None):
        if href.startswith('mailto:'):
            title = href[7:]
            return rf'\href{{ {href} }}{{\small\nolinkurl{{ {title} }}}}'

        else:
            if title is not None:
                return rf'\href{{ {href} }}{{ {title} }}'
            else:
                return rf'\mbox{{ \small\url{{ {href} }} }}'

    def pub(title, author, url, doi):
        return rf'\citembullet {title}'

    def project(content, **_):
        return rf'\citembullet {content}'

    def section(title, subtitle, content, **_):
        return tw.dedent(rf"""
        \citem{{{title}}}\\
        \textit{{{subtitle}}}\\
        {{{content}}}
        """)

    # TODO need to replaces "{{" "{%" etc in yaml file
    env_params = {
        'block_start_string'    : '[%',
        'block_end_string'      : '%]',
        'variable_start_string' : '[[',
        'variable_end_string'   : ']]',
    }

    templates = {'resume.tex' : f'{THISDIR}/resources/resume.tex.template'}

    return env_params, {
        'templates'   : templates,
        'url_raw'     : url,
        'bold'        : bold,
        'b'           : bold,
        'italic'      : italic,
        'i'           : italic,
        'code'        : code,
        'c'           : code,
        'pub_raw'     : pub,
        'project_raw' : project,
        'section'     : section
    }


def render(contents, env_params, renderer):

    def url(href, title=None):
        href = contents['urls'].get(href, href)
        return renderer['url_raw'](href, title)

    def pub(pid):
        details = contents['publications'][pid]
        return renderer['pub_raw'](**details)

    def project(pid):
        details = contents['projects'][pid]
        return renderer['project_raw'](**details)

    renderer = dict(renderer)
    renderer.update({
        'url'          : url,
        'pub'          : pub,
        'project'      : project,
        'urls'         : contents['urls'],
        'publications' : contents['publications'],
    })

    env = j2.Environment(**env_params)

    # pre-render project contents
    projects = dict(contents['projects'])
    for name, proj in dict(projects).items():
        if isinstance(proj, str):
            proj = env.from_string(proj)
            proj = {'content' : proj.render(**renderer)}
        else:
            proj            = dict(proj)
            content         = env.from_string(proj['content'])
            proj['content'] = content.render(**renderer)
        projects[name] = proj
    contents['projects'] = projects

    # pre-render section contents
    sections = list(contents['sections'])
    for i, sect in enumerate(sections):
        sect            = dict(sect)
        content         = env.from_string(sect['content'])
        content         = content.render(**renderer)
        sect['content'] = content
        sections[i]     = renderer['section'](**sect)
    contents['sections'] = sections

    # render abstract
    abstract = env.from_string(contents['abstract'])
    abstract = abstract.render(**renderer)

    renderer.update({
        'abstract' : abstract,
        'sections' : sections,
        'front'    : contents['front'],
    })

    rendered = {}

    for filename, template in renderer['templates'].items():
        with open(template, 'rt') as f:
            template = env.from_string(f.read())
        rendered[filename] = template.render(**renderer)

    return rendered

def main():
    if len(sys.argv) != 4:
        print('Usage: render.py infile outdir format')
        sys.exit(1)

    infile = sys.argv[1]
    outdir = sys.argv[2]
    format = sys.argv[3]

    if   format == 'html':  env_params, renderer = html()
    elif format == 'latex': env_params, renderer = latex()
    else: raise RuntimeError(f'Unrecognised output format: {format}')

    with open(infile, 'rt') as f:
        contents = yaml.load(f.read(), Loader=yaml.Loader)

    rendered = render(contents, env_params, renderer)

    for filename, file_contents in rendered.items():
        with open(f'{outdir}/{filename}', 'wt') as f:
            f.write(file_contents)


if __name__ == '__main__':
    main()
