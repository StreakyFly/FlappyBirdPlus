class MenuManager:
    def __init__(self):
        self.menu_stack = []

    @property
    def current_menu(self):
        if self.menu_stack:
            return self.menu_stack[-1]
        return None

    def push_menu(self, menu):
        self.menu_stack.append(menu)

    def pop_menu(self):
        if self.menu_stack:
            self.menu_stack.pop()

    def handle_event(self, event):
        if self.current_menu:
            self.current_menu.handle_event(event)

    def tick(self):
        if self.current_menu:
            self.current_menu.tick()

    def draw(self):
        if self.current_menu:
            self.current_menu.draw()
