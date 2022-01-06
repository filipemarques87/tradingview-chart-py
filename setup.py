from setuptools import setup

# pip install .
setup(
    name='pytvchart',
    version='0.1',
    description='',
    author='Filipe Marques',
    author_email='ft2m1987@gmal.com',
    packages=['pytvchart'],  # same as name
    # external packages as dependencies
    install_requires=['pywebview', 'numpy'],
)
