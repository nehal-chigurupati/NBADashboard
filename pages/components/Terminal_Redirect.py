import contextlib
from functools import wraps
from io import StringIO

import streamlit as st

def capture_output(func):
    """Capture output from running a function and write using streamlit."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Redirect output to string buffers
        stdout, stderr = StringIO(), StringIO()
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                return func(*args, **kwargs)
        except Exception as err:
            st.write(f"Failure while executing: {err}")
        finally:
            if _stdout := stdout.getvalue():
                with st.expander("Optimization Params"):
                    st.code(_stdout)
            if _stderr := stderr.getvalue():
                with st.expander("Optimization Error"):
                    st.code(_stderr)

    return wrapper