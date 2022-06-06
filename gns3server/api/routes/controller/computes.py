#
# Copyright (C) 2020 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
API routes for computes.
"""

from fastapi import APIRouter, Depends, Response, status
from typing import List, Union, Optional
from uuid import UUID

from gns3server.controller import Controller
from gns3server.db.repositories.computes import ComputesRepository
from gns3server.services.computes import ComputesService
from gns3server import schemas

from .dependencies.database import get_repository

responses = {404: {"model": schemas.ErrorMessage, "description": "Compute not found"}}

router = APIRouter(responses=responses)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.Compute,
    responses={
        404: {"model": schemas.ErrorMessage, "description": "Could not connect to compute"},
        409: {"model": schemas.ErrorMessage, "description": "Could not create compute"},
        401: {"model": schemas.ErrorMessage, "description": "Invalid authentication for compute"},
    },
)
async def create_compute(
    compute_create: schemas.ComputeCreate,
    computes_repo: ComputesRepository = Depends(get_repository(ComputesRepository)),
    connect: Optional[bool] = False
) -> schemas.Compute:
    """
    Create a new compute on the controller.
    """

    return await ComputesService(computes_repo).create_compute(compute_create, connect)


@router.post("/{compute_id}/connect", status_code=status.HTTP_204_NO_CONTENT)
async def connect_compute(compute_id: Union[str, UUID]) -> Response:
    """
    Connect to compute on the controller.
    """

    compute = Controller.instance().get_compute(str(compute_id))
    if not compute.connected:
        await compute.connect(report_failed_connection=True)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{compute_id}", response_model=schemas.Compute, response_model_exclude_unset=True)
async def get_compute(
    compute_id: Union[str, UUID], computes_repo: ComputesRepository = Depends(get_repository(ComputesRepository))
) -> schemas.Compute:
    """
    Return a compute from the controller.
    """

    return await ComputesService(computes_repo).get_compute(compute_id)


@router.get("", response_model=List[schemas.Compute], response_model_exclude_unset=True)
async def get_computes(
    computes_repo: ComputesRepository = Depends(get_repository(ComputesRepository)),
) -> List[schemas.Compute]:
    """
    Return all computes known by the controller.
    """

    return await ComputesService(computes_repo).get_computes()


@router.put("/{compute_id}", response_model=schemas.Compute, response_model_exclude_unset=True)
async def update_compute(
    compute_id: Union[str, UUID],
    compute_update: schemas.ComputeUpdate,
    computes_repo: ComputesRepository = Depends(get_repository(ComputesRepository)),
) -> schemas.Compute:
    """
    Update a compute on the controller.
    """

    return await ComputesService(computes_repo).update_compute(compute_id, compute_update)


@router.delete("/{compute_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_compute(
    compute_id: Union[str, UUID], computes_repo: ComputesRepository = Depends(get_repository(ComputesRepository))
) -> Response:
    """
    Delete a compute from the controller.
    """

    await ComputesService(computes_repo).delete_compute(compute_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{compute_id}/{emulator}/images")
async def get_images(compute_id: Union[str, UUID], emulator: str) -> List[str]:
    """
    Return the list of images available on a compute for a given emulator type.
    """

    controller = Controller.instance()
    compute = controller.get_compute(str(compute_id))
    return await compute.images(emulator)


@router.get("/{compute_id}/{emulator}/{endpoint_path:path}")
async def forward_get(compute_id: Union[str, UUID], emulator: str, endpoint_path: str) -> dict:
    """
    Forward a GET request to a compute.
    Read the full compute API documentation for available routes.
    """

    compute = Controller.instance().get_compute(str(compute_id))
    result = await compute.forward("GET", emulator, endpoint_path)
    return result


@router.post("/{compute_id}/{emulator}/{endpoint_path:path}")
async def forward_post(compute_id: Union[str, UUID], emulator: str, endpoint_path: str, compute_data: dict) -> dict:
    """
    Forward a POST request to a compute.
    Read the full compute API documentation for available routes.
    """

    compute = Controller.instance().get_compute(str(compute_id))
    return await compute.forward("POST", emulator, endpoint_path, data=compute_data)


@router.put("/{compute_id}/{emulator}/{endpoint_path:path}")
async def forward_put(compute_id: Union[str, UUID], emulator: str, endpoint_path: str, compute_data: dict) -> dict:
    """
    Forward a PUT request to a compute.
    Read the full compute API documentation for available routes.
    """

    compute = Controller.instance().get_compute(str(compute_id))
    return await compute.forward("PUT", emulator, endpoint_path, data=compute_data)


@router.post("/{compute_id}/dynamips/auto_idlepc")
async def dynamips_autoidlepc(compute_id: Union[str, UUID], auto_idle_pc: schemas.AutoIdlePC) -> str:
    """
    Find a suitable Idle-PC value for a given IOS image. This may take a few minutes.
    """

    controller = Controller.instance()
    return await controller.autoidlepc(str(compute_id), auto_idle_pc.platform, auto_idle_pc.image, auto_idle_pc.ram)
