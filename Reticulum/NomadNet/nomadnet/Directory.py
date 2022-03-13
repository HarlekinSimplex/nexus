import os
import RNS
import LXMF
import time
import nomadnet
import RNS.vendor.umsgpack as msgpack

class Directory:
    ANNOUNCE_STREAM_MAXLENGTH = 64

    aspect_filter = "nomadnetwork.node"
    @staticmethod
    def received_announce(destination_hash, announced_identity, app_data):
        app = nomadnet.NomadNetworkApp.get_shared_instance()
        destination_hash_text = RNS.hexrep(destination_hash, delimit=False)

        associated_peer = RNS.Destination.hash_from_name_and_identity("lxmf.delivery", announced_identity)

        app.directory.node_announce_received(destination_hash, app_data, associated_peer)
        app.autoselect_propagation_node()


    def __init__(self, app):
        self.directory_entries = {}
        self.announce_stream = []
        self.app = app
        self.load_from_disk()


    def save_to_disk(self):
        try:
            packed_list = []
            for source_hash in self.directory_entries:
                e = self.directory_entries[source_hash]
                packed_list.append((e.source_hash, e.display_name, e.trust_level, e.hosts_node, e.preferred_delivery))

            directory = {
                "entry_list": packed_list,
                "announce_stream": self.announce_stream
            }

            file = open(self.app.directorypath, "wb")
            file.write(msgpack.packb(directory))
            file.close()
        except Exception as e:
            RNS.log("Could not write directory to disk. Then contained exception was: "+str(e), RNS.LOG_ERROR)

    def load_from_disk(self):
        if os.path.isfile(self.app.directorypath):
            try:
                file = open(self.app.directorypath, "rb")
                unpacked_directory = msgpack.unpackb(file.read())
                unpacked_list = unpacked_directory["entry_list"]
                file.close()

                entries = {}
                for e in unpacked_list:
                    if len(e) > 3:
                        hosts_node = e[3]
                    else:
                        hosts_node = False

                    if len(e) > 4:
                        preferred_delivery = e[4]
                    else:
                        preferred_delivery = None

                    entries[e[0]] = DirectoryEntry(e[0], e[1], e[2], hosts_node, preferred_delivery=preferred_delivery)

                self.directory_entries = entries

                self.announce_stream = unpacked_directory["announce_stream"]


            except Exception as e:
                RNS.log("Could not load directory from disk. The contained exception was: "+str(e), RNS.LOG_ERROR)

    def lxmf_announce_received(self, source_hash, app_data):
        if app_data != None:
            timestamp = time.time()
            self.announce_stream.insert(0, (timestamp, source_hash, app_data, False))
            while len(self.announce_stream) > Directory.ANNOUNCE_STREAM_MAXLENGTH:
                self.announce_stream.pop()
            self.app.ui.main_display.sub_displays.network_display.directory_change_callback()

    def node_announce_received(self, source_hash, app_data, associated_peer):
        if app_data != None:
            timestamp = time.time()
            self.announce_stream.insert(0, (timestamp, source_hash, app_data, True))
            while len(self.announce_stream) > Directory.ANNOUNCE_STREAM_MAXLENGTH:
                self.announce_stream.pop()

            if self.trust_level(associated_peer) == DirectoryEntry.TRUSTED:
                existing_entry = self.find(source_hash)
                if not existing_entry:
                    node_entry = DirectoryEntry(source_hash, display_name=app_data.decode("utf-8"), trust_level=DirectoryEntry.TRUSTED, hosts_node=True)
                    self.remember(node_entry)
            
            self.app.ui.main_display.sub_displays.network_display.directory_change_callback()

    def remove_announce_with_timestamp(self, timestamp):
        selected_announce = None
        for announce in self.announce_stream:
            if announce[0] == timestamp:
                selected_announce = announce

        if selected_announce != None:
            self.announce_stream.remove(selected_announce)

    def display_name(self, source_hash):
        if source_hash in self.directory_entries:
            return self.directory_entries[source_hash].display_name
        else:
            return None

    def simplest_display_str(self, source_hash):
        trust_level = self.trust_level(source_hash)
        if trust_level == DirectoryEntry.WARNING or trust_level == DirectoryEntry.UNTRUSTED:
            return "<"+RNS.hexrep(source_hash, delimit=False)+">"
        else:
            if source_hash in self.directory_entries:
                return self.directory_entries[source_hash].display_name
            else:
                return "<"+RNS.hexrep(source_hash, delimit=False)+">"

    def alleged_display_str(self, source_hash):
        if source_hash in self.directory_entries:
            return self.directory_entries[source_hash].display_name
        else:
            return None


    def trust_level(self, source_hash, announced_display_name=None):
        if source_hash in self.directory_entries:
            if announced_display_name == None:
                return self.directory_entries[source_hash].trust_level
            else:
                for entry in self.directory_entries:
                    e = self.directory_entries[entry]
                    if e.display_name == announced_display_name:
                        if e.source_hash != source_hash:
                            return DirectoryEntry.WARNING

                return self.directory_entries[source_hash].trust_level
        else:
            return DirectoryEntry.UNKNOWN

    def preferred_delivery(self, source_hash):
        if source_hash in self.directory_entries:
            return self.directory_entries[source_hash].preferred_delivery
        else:
            return DirectoryEntry.DIRECT

    def remember(self, entry):
        self.directory_entries[entry.source_hash] = entry

        identity = RNS.Identity.recall(entry.source_hash)
        if identity != None:
            associated_node = RNS.Destination.hash_from_name_and_identity("nomadnetwork.node", identity)
            if associated_node in self.directory_entries:
                node_entry = self.directory_entries[associated_node]
                node_entry.trust_level = entry.trust_level

    def forget(self, source_hash):
        if source_hash in self.directory_entries:
            self.directory_entries.pop(source_hash)

    def find(self, source_hash):
        if source_hash in self.directory_entries:
            return self.directory_entries[source_hash]
        else:
            return None

    def is_known(self, source_hash):
        try:
            self.source_identity = RNS.Identity.recall(source_hash)

            if self.source_identity:
                return True
            else:
                return False

        except Exception as e:
            return False

    def known_nodes(self):
        node_list = []
        for eh in self.directory_entries:
            e = self.directory_entries[eh]
            if e.hosts_node:
                node_list.append(e)

        return node_list

    def number_of_known_nodes(self):
        return len(self.known_nodes())

    def number_of_known_peers(self, lookback_seconds=None):
        unique_hashes = []
        cutoff_time = time.time()-lookback_seconds
        for entry in self.announce_stream:
            if not entry[1] in unique_hashes:
                if lookback_seconds == None or entry[0] > cutoff_time:
                    unique_hashes.append(entry[1])

        return len(unique_hashes)

class DirectoryEntry:
    WARNING   = 0x00
    UNTRUSTED = 0x01
    UNKNOWN   = 0x02
    TRUSTED   = 0xFF

    DIRECT     = 0x01
    PROPAGATED = 0x02

    def __init__(self, source_hash, display_name=None, trust_level=UNKNOWN, hosts_node=False, preferred_delivery=None):
        if len(source_hash) == RNS.Identity.TRUNCATED_HASHLENGTH//8:
            self.source_hash  = source_hash
            self.display_name = display_name
            if display_name  == None:
                display_name  = source_hash

            if preferred_delivery == None:
                self.preferred_delivery = DirectoryEntry.DIRECT
            else:
                self.preferred_delivery = preferred_delivery

            self.trust_level  = trust_level
            self.hosts_node   = hosts_node
        else:
            raise TypeError("Attempt to add invalid source hash to directory")