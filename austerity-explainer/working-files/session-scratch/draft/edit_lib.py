import sys
GUIDE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/slate_layers/05 Recipe - slate in layers - how it is made.md'
class Doc:
    def __init__(self, path):
        self.path = path
        self.text = open(path).read()
    def rep(self, old, new, count=1):
        n = self.text.count(old)
        if n != count:
            print('PROBLEM: expected', count, 'found', n, 'for:', old[:90].replace('\n', ' | '))
            sys.exit(1)
        self.text = self.text.replace(old, new)
    def save(self):
        open(self.path, 'w').write(self.text)
