def pytest_addoption(parser):
    parser.addoption('--jenkins-docker', action='store',
                     default='jenkins/jenkins',
                     help='The Jenkins Docker container to launch')
