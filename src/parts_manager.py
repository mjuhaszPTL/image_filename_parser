# -*- coding: utf-8 -*-
"""
Parts data manager to manage part metadata.
"""

__project__ = "WeBuyBricks Lego Sorting"
__author__ = "Marcell Juhasz"
__copyright__ = """
    Copyright (c) 2023 Peacock Technology Limited or its suppliers.
    All rights reserved.

    This software is protected by national and international copyright and
    other laws. Unauthorised use, storage, reproduction, transmission
    and/or distribution of this software, or any part of it, may result in
    civil and/or criminal proceedings.

    This software is confidential and should not be disclosed, in whole or
    in part, to any person without the prior written permission of
    Peacock Technology Limited.
"""

import json
import logging

# PARTS = "data/parts.json"

# Uses rebrickable ids with rebrickable category
# PARTS = "data/parts_rebrickable_category.json"

# Uses bricklink ids with rebrickable category
PARTS = "data/parts_bricklink_id_rebrickable_category.json"


class PartsManager:
    _instance = None
    _initialized = False
    _parts_list = None

    def __new__(cls):
        if cls._instance is None:
            logging.info("Creating a new instance of PartsDataManager.")
            cls._instance = super().__new__(cls)
            cls._parts_list = None
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.load(PARTS)
            self._keywords = None
            self._categories = None
            self._parts = None
            self._names = None
            # self._process()
            self._initialized = True

    def load(self, json_file_path):
        with open(json_file_path, "r") as json_file:
            self._parts_list = json.load(json_file)

    def _process(self):
        categories = {data["category"]: 1 for data in self._parts_list}
        self._categories = [
            key for key in categories.keys() if key is not None
        ]
        self._categories.sort()

        keywords = {}
        for data in self._parts_list:
            if data["keywords"] is not None:
                for keyword in data["keywords"]:
                    if keyword is not None:
                        if keyword not in keywords:
                            keywords[keyword] = 0
                        keywords[keyword] += 1
        keywords = {
            keyword
            for (keyword, count) in keywords.items()
            if count > 2 and self._good_keyword(keyword)
        }
        self._keywords = list(keywords)
        self._keywords.sort()

        self._parts = {}
        self._names = []

        for index, part in enumerate(self._parts_list):
            self._parts[part["name"]] = index
            part["index"] = index

            if part["keywords"] is not None:
                part["keywords"] = {
                    k
                    for k in part["keywords"]
                    if k is not None and k in keywords
                }
            else:
                part["keywords"] = set()

            self._names.append(part["name"])

    def get_parts(self):
        if self._parts is None:
            return []
        return self._parts

    def get_parts_list(self):
        return self._parts_list

    def get_categories(self):
        if self._categories is None:
            return []
        return self._categories

    def _good_keyword(self, keyword):
        if (
            keyword.startswith("bricklink ")
            or keyword.startswith("rebrickable ")
            or keyword.startswith("set ")
        ):
            return False
        return True

    def get_keywords(self):
        if self._keywords is None:
            return []
        return self._keywords

    def get_names(self):
        if self._names is None:
            return []
        return self._names

    def get_index_by_name(self, part_id):
        index = self._parts[part_id]
        return index

    def get_part_data_by_name(self, part_name):
        part_info = next(
            (part for part in self._parts_list if part["name"] == part_name),
            None,
        )
        return part_info

    def get_part_data_by_index(self, index):
        if self._parts_list is None:
            return None
        if 0 <= index < len(self._parts_list):
            return self._parts_list[index]
        else:
            return None

    def get_part_metadata(self, part):
        """Get the metadata for a part."""
        if isinstance(part, str):
            return self.get_part_data_by_name(part)
        elif isinstance(part, int):
            return self.get_part_data_by_index(part)
        else:
            raise ValueError("Invalid part input. Expected string or integer.")

    def get_rebrickable_ids_with_category(self):
        rebrickable_id_category = [
            (part["rebrickable_id"], part["category"])
            for part in self._parts_list
            if part.get("rebrickable_id") is not None and part.get("category") is not None
        ]
        return rebrickable_id_category

    def get_category_by_rebricakble_id(self, rebrickable_id):
        # get category based on provided rebrickable_id
        for part in self._parts_list:
            if part.get("rebrickable_id") == rebrickable_id or part.get("name") == rebrickable_id:
                return part.get("category")

    def get_category_by_bricklink_id(self, bricklink_id):
        # get category based on provided bricklink_id
        for part in self._parts_list:
            if part.get("code") == bricklink_id:
                return part.get("category_name")
