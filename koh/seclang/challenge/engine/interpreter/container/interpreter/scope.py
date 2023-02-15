class Scope(object):
    def __init__(self):
        self.var_list = {}
        self.child_scopes = {0: True}
        self.top_scope = 0
        self.top_branch = 0

    def has(self, var_name):
        """Check if a variable is defined in this scope
        """
        return var_name in self.var_list

    def get(self, var_name):
        """Get a variable
        """
        if self.has(var_name):
            return self.var_list[var_name]
        else:
            raise RuntimeError(f"'{var_name}' not defined in this scope")

    def set(self, var_name, var_data):
        """Set a variable
        """
        if self.has(var_name):
            self.assign(var_name, var_data)
        else:
            self.define(var_name, var_data)

    def define(self, var_name, var_data):
        """Define a new variable
        This method throws error if the variable has already been defined.
        """
        if self.has(var_name):
            raise RuntimeError(f"Second definition of '{var_name}'")
        else:
            self.assign(var_name, var_data)

    def assign(self, var_name, var_data):
        """Assign data to a variable
        This method overwrites the variable if it has already been defined.
        """
        self.var_list[var_name] = var_data

    def create_child_scope(self):
        """Create a child scope for break statement
        """
        self.top_scope += 1
        self.child_scopes[self.top_scope] = True
        return self.top_scope

    def destroy_child_scope(self, scope_id):
        """Destroy child scope
        """
        assert self.top_scope == scope_id
        self.top_scope -= 1
        del self.child_scopes[scope_id]

    def is_child_scope_active(self, scope_id):
        """Check if break statement occur in this scope
        """
        return self.child_scopes[scope_id]

    def is_top_scope_active(self):
        return self.child_scopes[self.top_scope]

    def break_scope(self):
        """Break scope
        """
        if self.top_scope == 0:
            return False
        self.child_scopes[self.top_scope] = False
        return True

    def return_function(self):
        """Return function
        """
        for scope_id in self.child_scopes:
            self.child_scopes[scope_id] = False

    def enter_branch(self):
        """Enter "if" statement block
        """
        self.top_branch += 1

    def exit_branch(self):
        """Exit "if" statement block
        """
        self.top_branch -= 1

    def in_branch(self):
        """Check if it's in "if" statement block
        """
        return self.top_branch > 0
