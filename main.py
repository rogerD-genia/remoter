import ssh
import project
import server
import select
import Queue

# create the remote connection
host_db = ssh.SSHConnectionDB()
host_db.create_connection('helix', 'helix')

# create the projects
project_db = project.SynchronizedProjectDB()
project_db.create_project('snail', '/Users/dettlofr/Projects/snail')
project_db.create_project('snail-tools', '/Users/dettlofr/Projects/snail-tools')
project_db.create_project('ac-analysis', '/Users/dettlofr/Projects/ac-analysis')
project_db.create_project('data-handling', '/Users/dettlofr/Projects/data-handling')

# add remotes to each project
project_db.get('snail').add_remote_build('helix', '/home/rogerd/Projects/snail', auto_update=True)
project_db.get('snail-tools').add_remote_build('helix', '/home/rogerd/Projects/snail-tools', auto_update=True)
project_db.get('ac-analysis').add_remote_build('helix', '/home/rogerd/Projects/ac-analysis', auto_update=True)
project_db.get('data-handling').add_remote_build('helix', '/home/rogerd/Projects/data-handling', auto_update=True)

class Main:
    def __init__(self):
        self.update_queue = Queue.Queue()

        self.host_db = ssh.SSHConnectionDB()
        self.project_db = project.SynchronizedProjectDB()

        for p in self.project_db.values():
            p.start_monitor(self)

        self.server = server.RemoterServer(self)

    def run(self):
        try:
            while True:
                (ready_read, ready_write, ready_xcept) = select.select([self.server.fd], [], [], 0.01)

                for i in ready_read:
                    self.server.handle_request()

                if not self.update_queue.empty():
                    # get a list of all the projects that need updating
                    project_list = []

                    try:
                        while True:
                            p = self.update_queue.get(block=False)
                            if p not in project_list:
                                project_list.append(p)
                    except Queue.Empty:
                        pass

                    for name in project_list:
                        p = self.project_db.get(name)
                        p.update_remotes(self)

        except KeyboardInterrupt:
            for p in projects:
                p.stop_monitor()
                p.sync_monitor()

m = Main()
m.run()
