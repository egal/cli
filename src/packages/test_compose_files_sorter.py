from src.packages.compose_files_sorter import ComposeFilesSorter


def test():
    sorter = ComposeFilesSorter()

    cases = [
        {
            "input": [],
            "expected": [],
        },
        {
            "input": ["docker-compose.yml"],
            "expected": ["docker-compose.yml"],
        },
        {
            "input": ["docker-compose.foo.yml", "docker-compose.yml"],
            "expected": ["docker-compose.yml", "docker-compose.foo.yml"],
        },
        {
            "input": [
                "docker-compose.@local.yml",
                "docker-compose.foo.yml",
                "docker-compose.yml",
            ],
            "expected": [
                "docker-compose.yml",
                "docker-compose.foo.yml",
                "docker-compose.@local.yml",
            ],
        },
        {
            "input": [
                "docker-compose.bar.@local.foo.yml",
                "docker-compose.bar.@local.yml",
                "docker-compose.foo.yml",
                "docker-compose.yml",
            ],
            "expected": [
                "docker-compose.yml",
                "docker-compose.foo.yml",
                "docker-compose.bar.@local.yml",
                "docker-compose.bar.@local.foo.yml",
            ],
        },
        {
            "input": [
                "./foo/bar/docker-compose.yml",
                "./foo/docker-compose.yml",
                "docker-compose.yml",
            ],
            "expected": [
                "docker-compose.yml",
                "./foo/docker-compose.yml",
                "./foo/bar/docker-compose.yml",
            ],
        },
    ]

    for case in cases:
        actual = case["input"]
        sorter.sort(actual)
        assert actual == case["expected"]
