import setuptools

with open("README.rst", 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='geonomics',
    version='0.0.1',
    author='Drew Hart',
    author_email='drew.hart@berkeley.edu',
    description='A Python package for simulating landscape genomics',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/drewhart/geonomics',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Natural Language :: English',
        'Topic :: Scientific/Engineering :: Bio-Informatics'
    ],
    keywords=('landscape genomics ecology evolution simulation model '
              'genetics model'),
    project_urls={
        'Documentation': 'PUTDOCURLHERE',
        'Methods Paper': 'URLTOMETHODSPAPERHERE',
        'Source': 'https://github.com/drewhart/geonomics',
        'Tracker': 'BUGTRACKERSITHERE',
    },
    install_requires=['numpy', 'matplotlib', 'pandas', 'scipy', 'sklearn',
                      'statsmodels', 'shapely', 'bitarray', 'vcf'],
    python_requires='>=3.5',
    packages_data={
        'example': ['yosemite_30yr_normals_90x90.tif']
    },
)