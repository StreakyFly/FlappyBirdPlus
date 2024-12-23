class MenuManager:
    def __init__(self):
        self.menu_stack = []

    def push_menu(self, menu):
        self.menu_stack.append(menu)

    def pop_menu(self):
        if self.menu_stack:
            self.menu_stack.pop()

    def current_menu(self):
        if self.menu_stack:
            return self.menu_stack[-1]
        return None

    def handle_event(self, event):
        current_menu = self.current_menu()
        if current_menu:
            current_menu.handle_event(event)

    def tick(self):
        current_menu = self.current_menu()
        if current_menu:
            current_menu.tick()

    def draw(self):
        current_menu = self.current_menu()
        if current_menu:
            current_menu.draw()
