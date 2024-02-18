# -*- coding: utf-8 -*-
# Copyright (c) CDU

"""Model Docstrings

"""


class SQL:
    __slots__ = ()
    VACUUM: str = "VACUUM;"


class Database:

    def execute(self, sql: str):
        pass

    def commit(self):
        pass

    def vacuum(self):
        """
        The VACUUM command rebuilds the database file, repacking it into a minimal amount of disk space.

        References:
            https://www.sqlite.org/lang_vacuum.html

        Returns: None
        """
        self.execute(SQL.VACUUM)
        self.commit()
