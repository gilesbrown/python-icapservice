from setuptools import setup


setup(
    name='icapservice',
    version='0.0.1',
    description='ICAP service library for Python',
    author='Giles Brown',
    author_email='giles_brown@hotmail.com',
    url='https://github.com/gilesbrown/icapservice',
    license='MIT',
    packages=['icapservice'],
    zip_safe=False,
    install_requires=['six'],
    include_package_data=True,
    package_data={'': ['LICENSE']},
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
