# Acknowledgement:  Bela Schaum
# Reference:        https://github.com/streamlit/streamlit/issues/268
# Acknowledgement:  asehmi
# https://discuss.streamlit.io/t/reduce-whitespace-from-top-of-the-page-in-sidebar-as-well-as-place-two-elements-next-to-each-other/19495/4

import streamlit as st
import io
import contextlib


class _Redirect:

    class IOStuff(io.StringIO):

        def __init__(self, trigger, max_buffer, buffer_separator):
            super().__init__()
            self._trigger = trigger
            self._max_buffer = max_buffer
            self._buffer_separator = buffer_separator

        def write(self, __s: str) -> int:
            if self._max_buffer:
                concatenated_len = super().tell() + len(__s)
                if concatenated_len > self._max_buffer:
                    rest = self.getvalue()[concatenated_len -
                                           self._max_buffer:]
                    if self._buffer_separator is not None:
                        rest = rest.split(self._buffer_separator, 1)[-1]
                    super().seek(0)
                    super().write(rest)
                    super().truncate(super().tell() + len(__s))
            res = super().write(__s)
            self._trigger(self.getvalue())
            return res

        def shallow_copy(self):
            return _Redirect.IOStuff(self._trigger, self._max_buffer,
                                     self._buffer_separator)

    def __init__(self,
                 stdout=None,
                 stderr=False,
                 format=None,
                 to=None,
                 max_buffer=None,
                 buffer_separator='\n'):
        self.io = _Redirect.IOStuff(self._write, max_buffer, buffer_separator)
        self.redirections = []
        self.st = None
        self.stderr = stderr is True
        self.stdout = stdout is True or (stdout is None and not self.stderr)
        self.format = format or 'code'
        self.to = to
        self.fun = None

        if not self.stdout and not self.stderr:
            raise ValueError("one of stdout or stderr must be True")

        if self.format not in ['text', 'markdown', 'latex', 'code', 'write']:
            raise ValueError(
                f"format need oneof the following: "
                f"{', '.join(['text', 'markdown', 'latex', 'code', 'write'])}")

        if self.to and (not hasattr(self.to, 'text')
                        or not hasattr(self.to, 'empty')):
            raise ValueError("'to' is not a streamlit container object")

    def __enter__(self):
        # print('Entering context manager')
        if self.st is not None:
            raise Exception("Already entered")
        to = self.to or st
        to.content = ''

        # to.text(
        #     f"Redirected output from "
        #     f"{'stdout and stderr' if self.stdout and self.stderr
        # else 'stdout' if self.stdout else 'stderr'}:"
        # )
        self.st = to.empty()

        if self.stdout:
            self.redirections.append(contextlib.redirect_stdout(self.io))
        if self.stderr:
            self.redirections.append(contextlib.redirect_stderr(self.io))

        self.fun = getattr(self.st, self.format)
        for redirection in self.redirections:
            redirection.__enter__()

        return self.io

    def __call__(self,
                 to=None,
                 format=None,
                 max_buffer=None,
                 buffer_separator='\n'):
        return _Redirect(self.stdout,
                         self.stderr,
                         format=format,
                         to=to,
                         max_buffer=max_buffer,
                         buffer_separator=buffer_separator)

    def __exit__(self, *exc):
        # print('Exiting context manager')
        res = None
        for redirection in self.redirections:
            res = redirection.__exit__(*exc)

        self._write(self.io.getvalue())

        self.redirections = []
        self.st = None
        self.fun = None
        self.io = self.io.shallow_copy()
        return res

    def _write(self, data):
        self.to.content = data
        self.fun(data)


stdout = _Redirect()
stderr = _Redirect(stderr=True)
stdouterr = _Redirect(stdout=True, stderr=True)
'''
# can be used as
import time
import sys
from random import getrandbits
import streamlit.redirect as rd
st.text('Suboutput:')
so = st.empty()
with rd.stdout, rd.stderr(format='markdown', to=st.sidebar):
    print("hello  ")
    time.sleep(1)
    i = 5
    while i > 0:
        print("**M**izu?  ", file=sys.stdout if getrandbits(1) else sys.stderr)
        i -= 1
        with rd.stdout(to=so):
            print(f" cica {i}")
        if i:
            time.sleep(1)
# '''

# Setting the page container style:

BACKGROUND_COLOR = 'white'
COLOR = 'black'
BACKGROUND_COLOR_SIDEBARNAV = 'grey'


def set_page_container_style(
    max_width: int = 1100,
    max_width_100_percent: bool = True,
    padding_top: int = 3,
    padding_right: int = 3,
    padding_left: int = 2,
    padding_bottom: int = 2,
    color: str = COLOR,
    background_color: str = BACKGROUND_COLOR,
):
    if max_width_100_percent:
        max_width_str = 'max-width: 100%;'
    else:
        max_width_str = f'max-width: {max_width}px;'
    st.markdown(
        f'''
            <style>
                [data-testid="stSidebar"] [data-testid="stSidebarNav"] ul{{
                    /* background-color: {BACKGROUND_COLOR_SIDEBARNAV}; */
                    /* {max_width_str}; */
                    padding-top: 1rem;
                }}
                [data-testid="stSidebar"] .block-container {{
                    margin-top: -1rem;
                }}
                .appview-container .main .block-container {{
                    /* {max_width_str}; */
                    padding-top: {padding_top}rem;
                    padding-right: {padding_right}rem;
                    padding-left: {padding_left}rem;
                    padding-bottom: {padding_bottom}rem;
                }}
                .appview-container .main {{
                    color: {color};
                    background-color: {background_color};
                }}
            </style>
            ''',
        unsafe_allow_html=True,
    )


''' This can be use in the page.py as:

import streamlit as st
from common import set_page_container_style

st.set_page_config(
    page_title='My App',
    layout='wide',
    page_icon=':rocket:'
)

set_page_container_style(
        max_width = 1100, max_width_100_percent = True,
        padding_top = 0, padding_right = 10, padding_left = 5,
        padding_bottom = 10
)

def about():
    st.sidebar.markdown('---')
    st.sidebar.info('Some info here...')

if __name__ == '__main__':
    st.sidebar.image('./images/logo.png', output_format='png')
    st.title('My Mega App')
    about()

'''
