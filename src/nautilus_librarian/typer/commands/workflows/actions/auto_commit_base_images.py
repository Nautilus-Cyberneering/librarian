import os
from typing import List

from nautilus_librarian.domain.file_locator import (
    file_locator,
    guard_that_base_image_exists,
)
from nautilus_librarian.mods.dvc.domain.api import DvcApiWrapper
from nautilus_librarian.mods.dvc.domain.utils import (
    extract_added_files_from_dvc_diff,
    extract_modified_files_from_dvc_diff,
    extract_deleted_files_from_dvc_diff,
    extract_renamed_files_from_dvc_diff
)
from nautilus_librarian.mods.git.domain.git_user import GitUser
from nautilus_librarian.mods.git.domain.repo import GitRepo
from nautilus_librarian.mods.namecodes.domain.filename import Filename
from nautilus_librarian.mods.namecodes.domain.filename_filters import filter_gold_images
from nautilus_librarian.typer.commands.workflows.actions.action_result import (
    ActionResult,
    Message,
    ResultCode,
)


def format_extracted_files(files):
    """
    Parses a list of images from dvc diff output in json format, filters the Gold
    images and returns a list of Filenames.
    """
    gold_images = filter_gold_images(files)
    return [Filename(gold_image) for gold_image in gold_images]


def get_new_gold_images_filenames_from_dvc_diff(dvc_diff) -> List[Filename]:
    return format_extracted_files(extract_added_files_from_dvc_diff(dvc_diff))


def get_modified_gold_images_filenames_from_dvc_diff(dvc_diff) -> List[Filename]:
    return format_extracted_files(extract_modified_files_from_dvc_diff(dvc_diff))


def get_deleted_gold_images_filenames_from_dvc_diff(dvc_diff) -> List[Filename]:
    return format_extracted_files(extract_deleted_files_from_dvc_diff(dvc_diff))


def get_renamed_gold_images_filenames_from_dvc_diff(dvc_diff) -> List[Filename]:
    return format_extracted_files(extract_renamed_files_from_dvc_diff(dvc_diff))


def files_to_commit(base_img_relative_path) -> List[str]:
    """
    Given the relative path of a Base image it returns the relative paths
    of the files we have to include in the git repo.

    For example:

    For the Base image "data/000001/42/000001-42.600.2.tif", these are
    the files tracked on the git repo:

    - data/000001/42/.gitignore
    - data/000001/42/000001-42.600.2.tif.dvc
    """
    base_img_dir = os.path.dirname(base_img_relative_path)

    filepaths = [
        f"{base_img_dir}/.gitignore",
        f"{base_img_relative_path}.dvc",
    ]

    return filepaths


def commit_base_image(git_repo_dir, base_img_relative_path, gnupghome, git_user):
    repo = GitRepo(git_repo_dir, git_user, gnupghome)

    return repo.commit(
        files_to_commit(base_img_relative_path),
        commit_message=f"feat: new base image: {os.path.basename(base_img_relative_path)}",
    )


def calculate_the_corresponding_base_image_from_gold_image(git_repo_dir, gold_image):
    """
    Returns the Base image path which correspond to the given Gold image.

    Code Review: LibraryFilePath class? and rename Filename to LibraryFilename?
    """
    corresponding_base_image = gold_image.generate_base_image_filename()
    corresponding_base_image_relative_path = (
        file_locator(corresponding_base_image) + "/" + str(corresponding_base_image)
    )
    corresponding_base_image_absolute_path = (
        git_repo_dir + "/" + corresponding_base_image_relative_path
    )
    return (
        corresponding_base_image_relative_path,
        corresponding_base_image_absolute_path,
    )


def process_added_base_images(gold_images_list, messages, git_repo_dir, gnupghome, git_user):
    
    for gold_image in gold_images_list:
        (
            base_img_relative_path,
            base_img_absolute_path,
        ) = calculate_the_corresponding_base_image_from_gold_image(
            git_repo_dir, gold_image
        )

        guard_that_base_image_exists(base_img_absolute_path)

        dvc_api_wrapper = DvcApiWrapper(git_repo_dir)
        dvc_api_wrapper.add(base_img_relative_path)
        dvc_api_wrapper.push(f"{base_img_relative_path}.dvc")

        commit_base_image(git_repo_dir, base_img_relative_path, gnupghome, git_user)

        messages.append(
            Message(
                f"New Gold image found: {gold_image} -> Base image: {base_img_relative_path} ✓"
            )
        )


def process_modified_base_images(gold_images_list, messages, git_repo_dir, gnupghome, git_user):
    return


def process_renamed_base_images(gold_images_list, messages, git_repo_dir, gnupghome, git_user):
    # See note at https://dvc.org/doc/command-reference/diff#example-renamed-files
    # dvc diff only detects files which have been renamed but are otherwise unmodified.
    # Also, remember to commit new and OLD pointers
    return


def process_deleted_base_images(gold_images_list, messages, git_repo_dir, gnupghome, git_user):
    return


def auto_commit_base_images(dvc_diff, git_repo_dir, gnupghome, git_user: GitUser):
    """
    Workflow step: auto-commit new Base images generated during the workflow execution
    in previous steps.

    Case 1. Added Gold images.
    For each added Gold image:
      [✓] 1. Calculate the corresponding Base image filename and filepath.
      [✓] 2. Check if the Base image exists.
      [✓] 3. Add the image to dvc.
      [✓] 4. Push the image to remote dvc storage.
      [✓] 5. Commit the image to the current branch with a signed commit.

    Points 2 to 5 are different depending on whether we are adding,
    modifying or renaming the Gold image.

    TODO:
    Case 2. Modified Gold images.
    For each modified Gold image:
      [ ] 1. ??
      [ ] 2. ...
      [ ] 3. ??
    Pending to define:
    https://github.com/Nautilus-Cyberneering/chinese-ideographs/pull/122#issuecomment-972844365

    Case 3. Renamed Gold images.
    For each renamed Gold image:
      [ ] 1. ??
      [ ] 2. ...
      [ ] 3. ??
    Pending to define:
    https://github.com/Nautilus-Cyberneering/chinese-ideographs/pull/122#issuecomment-972844365
    """
    
    messages = []

    new_gold_images = get_new_gold_images_filenames_from_dvc_diff(dvc_diff)
    process_added_base_images(new_gold_images, messages, git_repo_dir, gnupghome, git_user)

    modified_gold_images = get_modified_gold_images_filenames_from_dvc_diff(dvc_diff)
    process_modified_base_images(modified_gold_images, messages, git_repo_dir, gnupghome, git_user)

    renamed_gold_images = get_renamed_gold_images_filenames_from_dvc_diff(dvc_diff)
    process_renamed_base_images(renamed_gold_images, messages, git_repo_dir, gnupghome, git_user)

    deleted_gold_images = get_deleted_gold_images_filenames_from_dvc_diff(dvc_diff)
    process_deleted_base_images(deleted_gold_images, messages, git_repo_dir, gnupghome, git_user)


    return ActionResult(ResultCode.CONTINUE, messages)
