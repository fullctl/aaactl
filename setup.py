from setuptools import find_packages, setup


def read_file(name):
    with open(name) as fobj:
        return fobj.read().strip()


VERSION = read_file("Ctl/VERSION")

#    packages=find_packages(),

setup(
    name="account_service",
    version=VERSION,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    #    scripts = ['manage.py'],
    entry_points={
        "console_scripts": [
            "account_service = account_service:manage",
            "manage = account_service:manage",
        ]
    },
)
