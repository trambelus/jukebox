"""The main entry for the jukebox."""

queue_file = 'queue.txt'

if __name__ == '__main__':
    import os
    import os.path
    from default_argparse import parser
    parser.add_argument('--host', default = '0.0.0.0', help = 'The interface on which to run the web server')
    parser.add_argument('-p', '--port', type = int, default = 80, help = 'The port to run the Jukebox on')
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
    try:
        from jukebox.api import api
    except ImportError as e:
        logging.critical(str(e))
        raise SystemExit
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
    if os.path.isfile(queue_file):
        from jukebox.metadata import get_track
        logging.info('Found queue file.')
        with open(queue_file, 'r') as f:
            for line in f.readlines():
                id = line.strip()
                try:
                    data = api.get_track_info(id)
                    track = get_track(data)
                    logging.info('Loading %r to the queue.')
                    app.queue.append(track)
                except Exception as e:
                    logging.info('Failed to get track with id %r:', id)
                    logging.exception(e)
                    continue
        os.remove(queue_file)
    else:
        logging.info('No queue file found.')
    try:
        app.run(args.host, args.port, logFile = args.log_file)
        if app.queue:
            with open(queue_file, 'w') as f:
                for track in app.queue:
                    f.write(track.id)
                    f.write('\n')
            logging.info('Dumped the queue.')
        else:
            logging.info('No queue to dump.')
    except Exception as e:
        logging.exception(e)
        logging.critical('Starting the app failed: %s.', e)
