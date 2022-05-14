def func_call(method):
    method(5,10)

class A:
    def __init__(self):
        self.val = []
    def callee(self, x=None, y=None):
        self.val.append(x)
        self.val.append(y)

a = A()
func = (lambda x=None, y=None : a.callee(x,y))
func_call(func)
print a.val

