from setuptools import setup, find_packages

setup(
    name = 'controller',
    author = 'Barbara Frosik',
    author_email = 'bfrosik@aps.anl.gov',
    description = 'Controller',
    packages = find_packages(),
    zip_safe = False,
    url='http://dquality.readthedocs.org',
    download_url='https://github.com/advancedPhotonSource/controller.git',
    license='BSD-3',
    platforms='Any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5']
)