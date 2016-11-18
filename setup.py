from setuptools import setup


setup(
    name="mos-scale-9.0",
    packages=["integrity_check"],
    entry_points={
        "console_scripts": [
            "connectivity_check=integrity_check.connectivity_check:main",
            "assign_floatingips=integrity_check.assign_floatingips:main",
        ]
    },
    install_requires=["pexpect"],
)
