from setuptools import setup


setup(
    name='ICAPuchin',
    version='0.0.1',
    description='ICAP server library for Python',
    author='Giles Brown',
    author_email='giles_brown@hotmail.com',
    url='https://github.com/gilesbrown/ICAPuchin',
    license='MIT',
    packages=['icapuchin'],
    zip_safe=False,
    install_requires=['six'],
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ),
)
