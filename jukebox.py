"""The main entry for the jukebox."""

if __name__ == '__main__':
    from default_argparse import parser
    parser.add_argument('--host', default = '0.0.0.0', help = 'The interface on which to run the web server')
    parser.add_argument('-p', '--port', type = int, default = 5853, help = 'The port to run the Jukebox on')
    parser.add_argument('-i', '--interval', type = float, default = 0.2, help = 'How often should the jukebox check the queue')
    parser.add_argument('-o', '--output-device', type = int, default = -1, help = 'The output device to use')
    parser.add_argument('--list-devices', action = 'store_true', help = 'List output devices')
    parser.add_argument('username', nargs = '?', help = 'Your google username')
    parser.add_argument('password', nargs = '?', help = 'Your Google password')
    args = parser.parse_args()
    if args.list_devices:
        print('Output devices:')
        import application
        for x, y in enumerate(application.output.get_device_names()):
            print('[%d] %s.' % (x + 1, y))
        raise SystemExit
    from configobj import ConfigObj
    config = ConfigObj('creds.ini')
    if args.username:
        config['username'] = args.username
    if not config.get('username'):
        config['username'] = input('Enter your Google username: ')
    if args.password:
        config['password'] = args.password
    if not config.get('password'):
        from getpass import getpass
        config['password'] = getpass('Password: ')
    config.write()
    import logging
    logging.basicConfig(stream = args.log_file, level = args.log_level, format = args.log_format)
    from jukebox.api import api
    logging.info('Loaded api %r.', api)
    from jukebox.app import app, play_manager
    import application
    if args.output_device == -1:
        application.output.set_device(application.output.find_default_device())
    else:
        from sound_lib.main import BassError
        try:
            application.output.set_device(args.output_device)
        except BassError:
            logging.critical('Invalid output device.')
            raise SystemExit
    logging.info('Using sound device %r.', application.output.get_device_names()[application.output.device - 1])
    from jukebox import pages
    logging.info('Loaded pages from %r.', pages)
    from twisted.internet.task import LoopingCall
    loop = LoopingCall(play_manager)
    args.interval = abs(args.interval)
    logging.info('Checking the queue every %.2f seconds.', args.interval)
    loop.start(args.interval)
    app.run(args.host, args.port, logFile = args.log_file)
