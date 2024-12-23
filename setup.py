from setuptools import setup, find_packages

setup(
    name="mafia-game",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        # 의존성 패키지 목록
    ],
    entry_points={
        "console_scripts": [
            "mafia-game=mafia.main:main",
        ],
    },
)
