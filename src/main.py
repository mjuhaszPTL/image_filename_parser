import os

import supervisely as sly
import supervisely.app.development as sly_app_development
import supervisely.app.widgets as widgets
from dotenv import load_dotenv

from .parts_manager import PartsManager

# Enabling advanced debug mode
if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))
    team_id = sly.env.team_id()
    workspace_id = sly.env.workspace_id()
    # project_id = sly.env.project_id()
    # dataset_id = sly.env.dataset_id()
    sly_app_development.supervisely_vpn_network(action="up")
    sly_app_development.create_debug_task(team_id, port="8000")

need_processing = widgets.Switch(switched=True)
parse_btn = widgets.Button("Parse filename")
stop_btn = widgets.Button("Stop")
processing_field = widgets.Field(
    title="Marcell's image filename processor",
    description="If turned on, the filename of the image will be parsed and the corresponding tags will be filled",
    content=need_processing,
)

progress_bar = widgets.Progress()
description_msg = widgets.Text()
finish_msg = widgets.Text(status="success")
select_dataset = widgets.SelectDataset(
    multiselect=True,
    select_all_datasets=True
)

layout = widgets.Container(
    widgets=[
        processing_field,
        select_dataset,
        parse_btn,
        stop_btn,
        progress_bar,
        description_msg,
        finish_msg,
    ]
)
app = sly.Application(layout=layout)
api = sly.Api.from_env()
stop_flag = False


@stop_btn.click
def stop_processing():
    global stop_flag
    stop_flag = True


@parse_btn.click
def parse_filename_and_update_tags():
    global stop_flag
    if not need_processing.is_on():
        # Checking if the processing is turned on in the UI.
        return

    sly.logger.info("Image opened, parsing filename and updating tags")

    selected_dataset_ids = select_dataset.get_selected_ids()
    selected_project_id = select_dataset.get_selected_project_id()
    if not selected_dataset_ids:
        sly.logger.warn("No dataset selected.")
        return
    if not selected_project_id:
        sly.logger.warn("No project selected.")
        return

    for selected_dataset_id in selected_dataset_ids:
        # Fetch the list of images in the dataset
        images_info = api.image.get_list(selected_dataset_id)
        total_images = len(images_info)

        with progress_bar(total=total_images) as pbar:
            # Iterate through each image in the dataset
            for image_info in images_info:
                if stop_flag:
                    # Stop processing if the flag is set
                    sly.logger.info("Processing stopped by user.")
                    break

                image_id = image_info.id
                image_name = image_info.name
                description_msg.set(f"Processing image {image_name}", "info")

                # Parse the filename
                parts = image_name.split("_")

                # Extract counter
                counter = int(parts[0])

                # Extract part_id
                part_id = parts[1].split("-")[0]

                # Extract color (if available)
                if len(parts) > 2:
                    color_parts = parts[1].split("-")[1:]
                    color = "-".join(color_parts)
                else:
                    color = ""

                # Extract camera_id
                camera_id = parts[-1].split(".")[0]

                parts_manager = PartsManager()
                category = parts_manager.get_category_by_rebricakble_id(part_id)
                if category is None:
                    category = "Other"

                sly.logger.info(
                    f"Image ID: {image_id}, "
                    f"Counter: {counter}, "
                    f"Part ID: {part_id}, "
                    f"Color: {color}, "
                    f"Camera ID: {camera_id}, "
                    f"Category: {category}"
                )

                # update_tags_custom_metadata(api, image_id, counter, part_id, color, camera_id)
                update_tags_annotation(
                    api,
                    selected_project_id,
                    image_id,
                    counter,
                    part_id,
                    color,
                    camera_id,
                    category
                )
                pbar.update(1)
            finish_msg.text = "Finished"
        stop_flag = False


def update_tags_custom_metadata(api, image_id, counter, part_id, color, camera_id):
    try:
        # Creating new tags based on the parsed values
        new_meta = {"counter": counter, "part_id": part_id, "color": color, "camera_id": camera_id}

        # Update the tags for the image in Supervisely platform
        api.image.update_meta(id=image_id, meta=new_meta)

        sly.logger.info(f"Tags updated successfully for image {image_id}")
    except Exception as e:
        sly.logger.error(f"Error updating tags for image {image_id}: {e}")


def update_tags_annotation(api, selected_project_id, image_id, counter, part_id, color, camera_id, category):
    try:
        global project_meta
        project_meta_json = api.project.get_meta(id=selected_project_id)
        project_meta = sly.ProjectMeta.from_json(data=project_meta_json)

        # Fetch existing annotations
        ann_json = api.annotation.download_json(image_id=image_id)
        ann = sly.Annotation.from_json(data=ann_json, project_meta=project_meta)

        counter_tag_meta = project_meta.get_tag_meta("counter")
        part_id_tag_meta = project_meta.get_tag_meta("part_id")
        color_tag_meta = project_meta.get_tag_meta("color")
        camera_tag_meta = project_meta.get_tag_meta("camera_id")
        category_tag_meta = project_meta.get_tag_meta("category")

        if counter_tag_meta or \
           part_id_tag_meta or \
           color_tag_meta or \
           camera_tag_meta or \
           category_tag_meta:
            ann = ann.delete_tag_by_name("counter")
            ann = ann.delete_tag_by_name("part_id")
            ann = ann.delete_tag_by_name("color")
            ann = ann.delete_tag_by_name("camera_id")
            ann = ann.delete_tag_by_name("category")
        else:
            counter_tag_meta = sly.TagMeta(
                name="counter",
                value_type=sly.TagValueType.ANY_NUMBER,
            )
            part_id_tag_meta = sly.TagMeta(
                name="part_id",
                value_type=sly.TagValueType.ANY_STRING,
            )
            color_tag_meta = sly.TagMeta(
                name="color",
                value_type=sly.TagValueType.ANY_STRING,
            )
            camera_tag_meta = sly.TagMeta(
                name="camera_id",
                value_type=sly.TagValueType.ONEOF_STRING,
                possible_values=["NORTH", "SOUTH", "EAST", "WEST", "TOP", "SIDE"],
            )
            category_tag_meta = sly.TagMeta(
                name="category",
                value_type=sly.TagValueType.ANY_STRING,
            )

            tag_metas = [
                counter_tag_meta,
                part_id_tag_meta,
                color_tag_meta,
                camera_tag_meta,
                category_tag_meta
            ]

            for tag_meta in tag_metas:
                if tag_meta not in project_meta.tag_metas:
                    project_meta = project_meta.add_tag_meta(new_tag_meta=tag_meta)
            api.project.update_meta(id=selected_project_id, meta=project_meta)
            project_meta_json = api.project.get_meta(id=selected_project_id)
            project_meta = sly.ProjectMeta.from_json(data=project_meta_json)

        counter_tag = sly.Tag(meta=counter_tag_meta, value=counter)
        part_id_tag = sly.Tag(meta=part_id_tag_meta, value=part_id)
        camera_id_tag = sly.Tag(meta=camera_tag_meta, value=camera_id)
        category_tag = sly.Tag(meta=category_tag_meta, value=category)

        tags = [counter_tag, part_id_tag, camera_id_tag, category_tag]
        if color:
            color_tag = sly.Tag(meta=color_tag_meta, value=color)
            tags.append(color_tag)
        else:
            sly.logger.warn(f"No color tag found for image {image_id}")

        ann = ann.add_tags(tags)

        # Update the tags for the given image in Supervisely
        api.annotation.upload_ann(img_id=image_id, ann=ann)

        # sly.logger.info(f"Tags updated successfully for image {image_id}")
    except Exception as e:
        sly.logger.error(f"Error updating tags for image {image_id}: {e}")
