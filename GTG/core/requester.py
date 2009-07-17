# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Gettings Things Gnome! - a personnal organizer for the GNOME desktop
# Copyright (c) 2008-2009 - Lionel Dricot & Bertrand Rousseau
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------


#Requester is a pure View object. It will not do anything but it will
#be used by any Interface to handle the requests to the datastore

#There could be multiple requester. It means that a requester should never
#Hold any data except a reference to its datastore.

class Requester :
    """A view on a GTG datastore.

    `Requester` is a stateless object that simply provides a nice API for user
    interfaces to use for datastore operations.

    Multiple `Requester`s can exist on the same datastore, so they should
    never have state of their own.
    """

    def __init__(self, datastore):
        """Construct a `Requester`."""
        self.ds = datastore

    def connect(self, signal, func):
        self.ds.connect(signal, func)

    ############## Tasks ##########################
    ###############################################

    def has_task(self, tid):
        """Does the task 'tid' exist?"""
        return self.ds.has_task(tid)

    def get_task(self, tid):
        """Get the task with the given 'tid'.

        If no such task exists, create it and force the tid to be 'tid'.

        :param tid: The task id.
        :return: A task.
        """
        task = self.ds.get_task(tid)
        return task

    def new_task(self, pid=None, tags=None, newtask=True):
        """Create a new task.

        Note: this modifies the datastore.

        :param pid: The project where the new task will be created.
        :param tags: The tags for the new task. If not provided, then the
            task will have no tags.
        :param newtask: 'True' if this is creating a task, 'False' if
            importing an existing task.
        """
        # XXX: The docs don't make it clear why you'd ever need to pass in
        # newtask or how newtask is used.
        task = self.ds.new_task(pid=pid, newtask=newtask)
        if tags:
            for t in tags:
                task.add_tag(t.get_name())
        return task

    def delete_task(self, tid):
        """Delete the task 'tid'.

        Note: this modifies the datastore.

        :param tid: The id of the task to be deleted.
        """
        self.ds.delete_task(tid)

    def get_tasks_list(self, tags=None, status=["Active"], notag_only=False,
                       started_only=True, is_root=False):
        """Return a list of tids of tasks.

        By default, returns a list of all the tids of all active tasks.

        :param tags: A list of tags. If provided, restricts the list of
            returned tasks to those that have one or more of these tags.
        :param status: A list of statuses. If provided, restricts the list of
            returned tasks to those that are in one of these states.
        :param notag_only: If True, only include tasks without tags. Defaults
            to False.
        :param started_only: If True, only include tasks that have been
            started. That is, tasks that have an already-passed start date or
            tasks with no startdate. Defaults to 'True'.
        :param is_root: If True, only include tasks that have no parent in the
            current selection. Defaults to False.

        :return: A list of task ids (tids).
        """
        l_tasks = []
        for tid in self.ds.all_tasks():
            task = self.get_task(tid)
            if task and not task.is_loaded():
                task = None
            # This is status filtering.
            if task and not task.get_status() in status:
                task = None
            # This is tag filtering.
            # If we still have a task and we need to filter tags
            # (if tags is None, this test is skipped)
            if task and tags:
                if not task.has_tags(tags):
                    task = None
                # Checking here the is_root because it has sense only with
                # tags.
                elif is_root and task.has_parents(tag=tags):
                    task = None
            #If tags = [], we still check the is_root.
            elif task and is_root:
                if task.has_parents():
                    # We accept children of a note.
                    for p in task.get_parents():
                        pp = self.get_task(p)
                        if pp.get_status() != "Note":
                            task = None
            # Now checking if it has no tag.
            if task and notag_only:
                if not task.has_tags(notag_only=notag_only):
                    task = None
            # This is started filtering.
            if task and started_only:
                if not task.is_started():
                    task = None

            # If we still have a task, we return it.
            if task:
                l_tasks.append(tid)
        return l_tasks

    def get_active_tasks_list(self, tags=None, notag_only=False,
                              started_only=True, is_root=False,
                              workable=False):
        """Return a list of task ids for all active tasks.

        See `get_tasks_list` for more information about the parameters.

        :param workable: If True, then only include tasks with no pending
            subtasks and that can be done directly and exclude any tasks that
            have a 'nonworkview' tag which is not explicitly provided in the
            'tags' parameter. Defaults to False.
        """
        l_tasks = []
        if workable:
            nonwork_tag = self.ds.get_tagstore().get_all_tags(
                attname="nonworkview", attvalue="True")
            # We build the list of tags we will skip.
            for nwtag in nonwork_tag:
                # If the tag is explicitly selected, it doesn't go in the
                # nonwork_tag.
                if tags and nwtag in tags:
                    nonwork_tag.remove(nwtag)
            # We build the task list.
            temp_tasks = self.get_active_tasks_list(
                tags=tags, notag_only=notag_only, started_only=True,
                is_root=False, workable=False)
            # Now we verify that the tasks are workable and don't have a
            # nonwork_tag.
            for tid in temp_tasks:
                t = self.get_task(tid)
                if t and t.is_workable():
                    if len(nonwork_tag) == 0:
                        l_tasks.append(tid)
                    elif not t.has_tags(nonwork_tag):
                        l_tasks.append(tid)
            return l_tasks
        else:
            active = ["Active"]
            temp_tasks = self.get_tasks_list(
                tags=tags, status=active, notag_only=notag_only,
                started_only=started_only, is_root=is_root)
            for t in temp_tasks:
                l_tasks.append(t)
            return l_tasks

    def get_closed_tasks_list(self, tags=None, notag_only=False,
                              started_only=False, is_root=False):
        """Return a list of task ids for closed tasks.

        "Closed" means either "done", "dismissed" or "deleted".

        See `get_tasks_list` for more information about the parameters.
        """
        closed = ["Done", "Dismiss", "Deleted"]
        return self.get_tasks_list(
            tags=tags, status=closed, notag_only=notag_only,
            started_only=started_only, is_root=is_root)

    def get_notes_list(self, tags=None, notag_only=False):
        """Return a list of task ids for notes.

        See `get_tasks_list` for more information about the parameters.
        """
        note = ["Note"]
        return self.get_tasks_list(
            tags=tags, status=note, notag_only=notag_only, started_only=False,
            is_root=False)


    ############### Tags ##########################
    ###############################################

    def new_tag(self, tagname):
        """Create a new tag called 'tagname'.

        Note: this modifies the datastore.

        :param tagname: The name of the new tag.
        :return: The newly-created tag.
        """
        return self.ds.get_tagstore().new_tag(tagname)

    def get_tag(self, tagname):
        return self.ds.get_tagstore().get_tag(tagname)

    def get_all_tags(self):
        """Return a list of every tag that was ever used."""
        return list(self.ds.get_tagstore().get_all_tags())
        
    def get_notag_tag(self) :
        return self.ds.get_tagstore().get_notag_tag()

    def get_alltag_tag(self):
        return self.ds.get_tagstore().get_alltag_tag()

    def get_used_tags(self):
        """Return tags currently used by a task.

        :return: A list of tags used by a task.
        """
        # FIXME: it should be only active and visible tasks.
        l = []
        for tid in self.ds.all_tasks():
            t = self.get_task(tid)
            if t:
                for tag in t.get_tags():
                    if tag not in l:
                        l.append(tag)
        return l