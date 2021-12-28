HOME_PATH = ''
IMAGE_PATH = ''
PRJ_PATH = ''

def run():
    from OpenNumismat.pathes import init_pathes
    init_pathes()

    from OpenNumismat.main import main
    main()
