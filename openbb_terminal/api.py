"""OpenBB Terminal API."""

import types
import functools
import importlib
from typing import Optional, Callable

"""
THIS IS SOME EXAMPLE OF USAGE FOR USING IT DIRECTLY IN JUPYTER NOTEBOOK
"""
shortcuts = {
    "stocks.get_news": {
        "model": "openbb_terminal.common.newsapi_model.get_news",
    },
    "economy.bigmac": {
        "model": "openbb_terminal.economy.nasdaq_model.get_big_mac_index",
        "view": "openbb_terminal.economy.nasdaq_view.display_big_mac_index",
    },
}
"""
api = APILoader(shortcuts=shortcuts)
api.stocks.get_news()
api.economy.bigmac(chart=True)
api.economy.bigmac(chart=False)


TO USE THE API DIRECTLY JUST IMPORT IT:
from openbb_terminal.api import api (or: from openbb_terminal.api import api as openbb)
"""


def copy_func(f: Callable) -> Callable:
    """Copies the contents and attributes of the entered function. Based on https://stackoverflow.com/a/13503277

    Parameters
    ----------
    f: Callable
        Function to be copied

    Returns
    -------
    g: Callable
        New function
    """
    g = types.FunctionType(
        f.__code__,
        f.__globals__,
        name=f.__name__,
        argdefs=f.__defaults__,
        closure=f.__closure__,
    )
    g = functools.update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    return g


def change_docstring(api_callable, model: Callable, view: Callable = None):
    if view is None:
        api_callable.__doc__ = model.__doc__
        api_callable.__name__ = model.__name__
    else:
        index = view.__doc__.find("Parameters")
        all_parameters = "\nAPI function, use the chart kwarg for getting the view model and it's plot. See every parmater below:\n\n\t" + view.__doc__[index:] + """chart: bool
    If the view and its chart shall be used"""
        api_callable.__doc__ = all_parameters + "\n\nModel doc:\n" + model.__doc__ + "\n\nView doc:\n" + view.__doc__
        api_callable.__name__ = model.__name__.replace("get_", "")

    return api_callable


class APIFactory:
    """The API Factory, which creates the callable instance"""
    def __init__(self, model: Callable, view: Callable = None):
        """Initialises the APIFactory instance

        Parameters
        ----------
        model: Callable
            The original model function from the terminal
        view: Callable
            The original view function from the terminal, this shall be set to None if the function has no charting
        """
        self.model_only = False
        if view is None:
            self.model_only = True
            self.model = copy_func(model)
        else:
            self.model = copy_func(model)
            self.view = copy_func(view)

    def api_callable(self, *args, **kwargs):
        """This returns the result of the command from the view or the model function based on the chart parameter

        Parameters
        ----------
        args
        kwargs

        Returns
        -------
        Result from the view or model
        """
        if "chart" not in kwargs:
            kwargs["chart"] = False
        if kwargs["chart"] and (not self.model_only):
            kwargs.pop("chart")
            return self.view(*args, **kwargs)
        else:
            kwargs.pop("chart")
            return self.model(*args, **kwargs)


class Item:
    def __init__(self, function: Callable):
        self.__function = function

    def __call__(self, *args, **kwargs):
        self.__function(*args, **kwargs)


class APILoader:
    """The APILoader class"""
    def __init__(self, shortcuts: dict):
        self.__mapping = self.build_mapping(shortcuts=shortcuts)
        self.load_items()

    def __call__(self):
        """Prints help message"""
        print("""This is the API of the OpenBB Terminal.
        
        Use the API to get data directly into your jupyter notebook or directly use it in your application.
        For documentation use: 
        - help(<api>.<menu>.<command>.<model or view>)
        - or: <api>.<menu>.<command>.<model or view>.__doc__
        
        Use <api>.settings() to change the settings of the api instance (for example: openbb.settings(bla bla)
        ...
        
        For more information see the official documentation at: https://openbb-finance.github.io/OpenBBTerminal/api/
        """)

    # TODO: Add settings
    def settings(self):
        pass

    def load_items(self):
        """Creates the API structure (see api.stocks.command) by setting attributes and saving the functions"""
        mapping = self.__mapping
        for shortcut, function in mapping.items():
            shortcut_split = shortcut.split(".")
            last_shortcut = shortcut_split[-1]

            previous = self
            for item in shortcut_split[:-1]:
                next_item = Item(function=item)
                previous.__setattr__(item, next_item)
                previous = next_item

            previous.__setattr__(last_shortcut, function)

    @staticmethod
    def load_module(module_path: str) -> Optional[types.ModuleType]:
        """Load a module from a path.
        Args:
            module_path (str):
                Module"s path.
        Returns:
            Optional[ModuleType]:
                Loaded module or None.
        """

        try:
            spec = importlib.util.find_spec(module_path)
        except ModuleNotFoundError:
            spec = None

        if spec is None:
            return None
        else:
            module = importlib.import_module(module_path)

            return module

    @staticmethod
    def get_function(cls, function_path: str) -> Callable:
        """Get function from string path

        Parameters
        ----------
        cls
            Class
        function_path: str
            Function path from repository base root

        Returns
        -------
        Callable
            Function
        """
        module_path, function_name = function_path.rsplit(sep=".", maxsplit=1)
        module = cls.load_module(module_path=module_path)

        return getattr(module, function_name)

    @classmethod
    def build_mapping(cls, shortcuts: dict) -> dict:
        """Builds dictionary with APIFactory instances as items

        Parameters
        ----------
        shortcuts: dict
            Dictionary which has string path of view and model functions as keys. The items is dictionary with the view and model function as items of the respectivee "view" and "model" keys

        Returns
        -------
        dict
            Dictionary with APIFactory instances as items and string path as keys
        """
        mapping = {}

        for shortcut in shortcuts.keys():
            model_path = shortcuts[shortcut].get("model")
            view_path = shortcuts[shortcut].get("view")

            if model_path:
                model_function = cls.get_function(cls, function_path=model_path)
            else:
                model_function = None

            if view_path:
                view_function = cls.get_function(cls, function_path=view_path)
            else:
                view_function = None

            api_factory = APIFactory(model=model_function, view=view_function)
            api_function = change_docstring(types.FunctionType(api_factory.api_callable.__code__, {}), model_function, view_function)
            mapping[shortcut] = types.MethodType(api_function, api_factory)

        return mapping


api = APILoader(shortcuts=shortcuts)
