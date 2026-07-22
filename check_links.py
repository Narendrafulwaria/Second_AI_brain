import frontmatter
import pathlib

notes = list(pathlib.Path('wiki').rglob('*.md'))
for f in notes:
    post = frontmatter.load(f)
    if post.get('links'):
        print(f'{f.name}: links={post.get("links")}')
        print(f'Content preview: {post.content[:200]}')
        print('---')
