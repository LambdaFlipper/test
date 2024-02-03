"""
Helper methods for retrieving simulation objects from lists or listing available entitities.

Author: elenia@TUBS
Copyright 2024 elenia
This file is part of eELib, which is free software under the terms of the GNU GPL Version 3.
"""

import mosaik
import logging
import os
from datetime import datetime

_logger = logging.getLogger(__name__)


def get_entity_by_id(e_list: list, e_id: str):
    """Provides an entity with regard to a given id from the entity list.

    Args:
        e_list (list): list of entities to be searched in
        e_id (str): id of the entity that we search for

    Returns:
        entity: model entity if found, otherwise None
        dict: dict for the model entity (eid, full_id, type) if found, otherwise None
    """

    # goes by each entity in the list separately and checks whether the name corresponds
    for entity in e_list:
        if entity.eid == e_id:
            # return the entity, if found
            return entity, {"eid": entity.eid, "full_id": entity.full_id, "type": entity.type}

    # entity was not found: return None
    return None, None


def get_entity_by_id_from_dict_list(e_dict_list: dict, e_id: str):
    """Provides an entity with regard to a given id from the entity list.

    Args:
        e_dict_list (dict): dict with lists of entities (sorted by type) to be searched in
        e_id (str): id of the entity that we search for

    Returns:
        entity: model entity if found, otherwise None
        dict: dict for the model entity (eid, full_id, type) if found, otherwise None
    """

    # go by each list stored in the dict and try to find the entity in the lists
    for e_list in e_dict_list.values():
        entity, ent_dict = get_entity_by_id(e_list=e_list, e_id=e_id)

        # return the entity, if found
        if entity is not None:
            return entity, ent_dict

    # entity was not found: return None
    return None, None


def create_plots(world: object, dir_graphs: str, bool_plot: bool, slices_execution: list = [0, 4]):
    """Create some plots after the simulation.
    Especially the execution_graph take some time to create and should not be created for every
    simulation.

    Args:
        world (object): mosaik world object to orchestrate the simulation process
        dir_graphs (str): direction where to save the create plots
        bool_plot (bool): whether to create the plots or not
        slices_execution (list): list of length 2 to assign start and end index of the execution
            graph to plot. Defaults to [0, 4].
    """
    if bool_plot:
        mosaik.util.plot_dataflow_graph(world, folder=dir_graphs)
        mosaik.util.plot_execution_graph(world, folder=dir_graphs, slice=slices_execution)
        mosaik.util.plot_execution_time(world, folder=dir_graphs)
        mosaik.util.plot_execution_time_per_simulator(world, folder=dir_graphs)


def start_simulators(sim_config: dict, world: object, scenario_config: dict) -> dict:
    """Start all model factories for the simulators listed in SIM_CONFIG and one for each model.

    Args:
        sim_config (dict): Information about the used simulators and their models
        world (object): mosaik world object to orchestrate the simulation process
        scenario_config (dict): parameters for the simulation scenario

    Returns:
        dict: Contains all ModelFactorys sorted by the name of the corresponding model
    """

    dict_simulators = {}

    for sim_name, sim_dict in sim_config.items():
        for model_name in sim_dict["models"].keys():
            dict_simulators[model_name] = world.start(sim_name, scenario_config=scenario_config)
            _logger.info(f"ModelFactory for {model_name} of simulator {sim_name} is started.")

    return dict_simulators


def create_entities(
    sim_config: dict, model_data: dict, dict_simulators: dict, grid_model_config: dict = {}
) -> dict:
    """Create all models based on simulators and their models dict given in sim_config.

    Args:
        sim_config (dict): Information about the used simulators and their models
        model_data (dict): dict containing all information about the to-be-created model entities
        dict_simulators (dict): dict of all used simulators with their ModelFactory-objects
        grid_model_config (dict): contains assigning the devices (by its type) to loads in the grid

    Raises:
        KeyError: If a model is to be created but does not exist for this simulator (ModelFactory)

    Returns:
        dict: contains all created entities sorted by their model type
    """

    dict_entities = {}

    # go by each simulator and its models given in sim_config
    for sim_name, sim_dict in sim_config.items():
        for model_name in sim_dict["models"].keys():
            if model_name == "ems":  # different handling for energy management system models
                # collect information about the used ems strategies by looking for model data
                num_ems_type = {}
                model_data_ems_type = {}
                for ems in model_data["ems"]:
                    if ems["strategy"] not in num_ems_type:
                        num_ems_type[ems["strategy"]] = 0
                    if ems["strategy"] not in model_data_ems_type:
                        model_data_ems_type[ems["strategy"]] = []
                    num_ems_type[ems["strategy"]] += 1
                    model_data_ems_type[ems["strategy"]].append(ems)
                # create all of the used ems models with their strategy
                for ems_strategy_name in model_data_ems_type.keys():
                    if not hasattr(dict_simulators[model_name], ems_strategy_name):
                        raise KeyError(f"ModelFactory {sim_name} has no model type {model_name}!")
                    dict_entities[ems["strategy"]] = create_entities_of_model(
                        model_factory=dict_simulators[model_name],
                        model_name=ems_strategy_name,
                        init_vals=model_data_ems_type[ems["strategy"]],
                    )
            else:
                # adaption for grid ems models: add grid model config
                if model_name == "GridEMS":
                    for i_model in range(len(model_data[model_name])):
                        model_data[model_name][i_model]["grid_model_config"] = grid_model_config

                # simply create the entities with the given simulator, the name and the model data
                dict_entities[model_name] = create_entities_of_model(
                    model_factory=dict_simulators[model_name],
                    model_name=model_name,
                    init_vals=model_data[model_name],
                )
            _logger.info(
                f"Models created for modeltype {model_name} with ModelFactory of {sim_name}."
            )

    return dict_entities


def create_entities_of_model(model_factory: object, model_name: str, init_vals: list) -> list:
    """Create model entities for a given ModelFactory object with regard to model name and input.

    Args:
        model_factory (object): ModelFactory for a model
        model_name (str): name of the model to create entities for
        init_vals (list): initial values of the model (attributes to set)

    Raises:
        KeyError: If the ModelFactory has no such model type
        TypeError: If the initial values were given in the wrong format

    Returns:
        list: all created model entities in one list (empty if no entity to create)
    """

    # check if model class is existing
    if not hasattr(model_factory, model_name):
        raise KeyError(f"The ModelFactory {model_factory} has no model type {model_name}")

    # check if initial model values are given correctly
    if not isinstance(init_vals, list):
        raise TypeError(f"Init values for {model_name} were given in wrong format, should be list")

    # if no entities should be created, return empty list
    if len(init_vals) == 0:
        return []

    # create the entities
    entity_list = getattr(model_factory, model_name).create(num=len(init_vals), init_vals=init_vals)

    return entity_list


def get_grid_components(grid_comps_list: list) -> dict:
    """Collect all components of a specific grid.

    Args:
        grid_comps_list (list): list of all grid components to collect from

    Returns:
        dict: containing all grid components separated by type
    """
    grid_comps = {}
    grid_comps["bus"] = [b for b in grid_comps_list if b.type in "bus"]
    grid_comps["load"] = [
        c for c in grid_comps_list if (c.type in "load") and ("ext_load" not in c.eid)
    ]
    grid_comps["trafo"] = [t for t in grid_comps_list if t.type in "trafo"]
    grid_comps["line"] = [t for t in grid_comps_list if t.type in "line"]
    grid_comps["ext_grid"] = [e for e in grid_comps_list if e.type in "ext_grid"]

    return grid_comps


def check_model_connect_config(model_connect_config: list):
    """Check the layout and input of a connection configuration for models.

    Args:
        model_connect_config (list): list of the model properties to connect

    Raises:
        TypeError: If the connection config is no list
        TypeError: If an element of the connection config is neither a string nor a tuple
        TypeError: If an connection config element is a tuple but not consisting of two strings
    """

    # check if connection configuration is a list of string values or tuples
    if not isinstance(model_connect_config, list):
        raise TypeError(
            f"Given connection configuration is not a list but a {type(model_connect_config)}"
        )
    else:
        for elem_connect in model_connect_config:
            if not isinstance(elem_connect, (str, tuple)):
                raise TypeError(
                    "Given connection config has an inaccessible element with the type"
                    f" {type(elem_connect)} that is not string or tuple"
                )
            elif isinstance(elem_connect, tuple) and (
                not isinstance(elem_connect[0], str) or not isinstance(elem_connect[1], str)
            ):
                raise TypeError(
                    "Given connection config has an inaccessible tuple element where one of the two"
                    " is not a string"
                )


def connect_entities(
    world: object, dict_entities: dict, model_connect_config: dict, dict_simulators: dict
):
    """Connect all model entities to each other based on the created models and their connections.

    Args:
        world (object): mosaik world object to orchestrate the simulation process
        dict_entities (dict): dict of all used model entity objects as lists, sorted by their type
        model_connect_config (dict): dict of all connected attributes between each model type
        dict_simulators (dict): dict of all used simulators with their ModelFactory-objects
    """
    # connect all models to each other (so check every combination of the entities)
    for idx_model_outer, model_name_from in enumerate(dict_entities.keys()):
        for idx_model_inner, model_name_to in enumerate(dict_entities.keys()):
            # only connect into one direction and also leave out connections to itself
            if idx_model_inner <= idx_model_outer:
                continue

            # check if one of the models is ems - should always have weak connection with set values
            if "ems" in model_name_from or "EMS" in model_name_from:
                sim_entities_weak = dict_simulators["ems"]

                # switch the direction
                name_from = model_name_to
                name_to = model_name_from
            elif "ems" in model_name_to or "EMS" in model_name_to:  # this direction is ok
                sim_entities_weak = dict_simulators["ems"]
                name_from = model_name_from
                name_to = model_name_to
            else:  # no ems is involved
                sim_entities_weak = None
                name_from = model_name_from
                name_to = model_name_to

                # check if charging station and electric vehicle are involved
                if "charging_station" in model_name_from and "car" in model_name_to:
                    # switch the direction
                    name_from = model_name_to
                    name_to = model_name_from

            # connect the two models with each other
            connect_entities_of_two_model_types(
                world,
                entity_list_strong=dict_entities[name_from],
                entity_list_weak=dict_entities[name_to],
                model_connect_config_from_strong=model_connect_config[name_from][name_to],
                model_connect_config_from_weak=model_connect_config[name_to][name_from],
                sim_entities_weak=sim_entities_weak,
            )

        # for the ems: add all the assigned evs to the ems control
        if "ems" in model_name_from or "EMS" in model_name_from:
            for ems_ent in dict_entities[model_name_from]:
                if "EV" in dict_entities.keys():
                    for ev_ent in dict_entities["EV"]:
                        ev_entity, ev_entity_dict = get_entity_by_id(
                            e_list=dict_entities["EV"], e_id=ev_ent.eid
                        )
                        dict_simulators["ems"].add_controlled_entity(
                            ems_ent.eid, {ev_entity.eid: ev_entity_dict}
                        )


def connect_entities_in_grid(
    grid_model_config: dict,
    grid: object,
    grid_loads: list,
    world: object,
    model_connect_config: dict,
    dict_entities: dict,
    dict_simulators: dict,
):
    """Connect all entities for a simulation containing a power grid.
    Includes connection between the devices in the grid and between devices (or EMS) and grid loads.

    Args:
        grid_model_config (dict): contains assigning the devices (by its type) to loads in the grid
        grid (object): power grid entity
        grid_loads (list): list of all load objects in the power grid
        world (object): mosaik world object to orchestrate the simulation process
        model_connect_config (dict): dict of all connected attributes between each model type
        dict_entities (dict): dict of all used model entity objects as lists, sorted by their type
        dict_simulators (dict): dict of all used simulators with their ModelFactory-objects

    Raises:
        KeyError: No entity was created for a desired connection in the grid
        ValueError: There are electric vehicles but no charging stations at a connection point.
        KeyError: A grid load is planned to be connected to two different entities
    """

    # get grid ems, if one is present
    grid_ems_present = False
    if "GridEMS" in dict_entities.keys():
        grid_ems_present = True
        grid_ems_ent = dict_entities["GridEMS"][0]

        # connect the grid to the grid ems
        world.connect(grid, grid_ems_ent, "grid_status", "ptdf_mat", "vpif_mat")
        _logger.info(f"Grid '{grid.eid}' connected to grid ems {grid_ems_ent.eid}.")

    # iterate over all grid connection points (gcp) which are connected to the entitites
    # NOTE: gcps are modeled as loads
    for gcp_id, gcp_dict in grid_model_config.items():
        # save the devices names
        ems_gcp_id = gcp_dict["ems"]
        del gcp_dict["ems"]

        # initialize empty dict of entity types (containing list of entities) at this gcp
        dict_ent_gcp = {}
        # add connected devices at this gcp to the entity dict
        for ent_id_list in gcp_dict.values():
            for ent_id in ent_id_list:
                ent, ent_dict = get_entity_by_id_from_dict_list(
                    e_dict_list=dict_entities, e_id=ent_id
                )

                # check if no entity was found
                if ent is None:
                    _logger.error(
                        f"Entity {ent_id} was given in grid_model_config at load {gcp_id} but"
                        " was not created for the simulation!"
                    )
                    raise KeyError(
                        f"Entity {ent_id} was given in grid_model_config at load {gcp_id} but"
                        " was not created for the simulation!"
                    )

                # check if type already existent in entity dict, otherwise create key
                if ent_dict["type"] not in dict_ent_gcp.keys():
                    dict_ent_gcp[ent_dict["type"]] = []

                dict_ent_gcp[ent_dict["type"]].append(ent)

        if len(gcp_dict["ev"]) > 0 and len(gcp_dict["cs"]) == 0:
            raise ValueError("No charging station for the electric vehicle(s)!")

        # find adjacent gcp in grid load
        for gcp in grid_loads:
            if gcp.eid == gcp_id:  # gcp is found, break the for loop
                break
        # go to the next load if this one was not found
        if not gcp.eid == gcp_id:
            return

        # check whether an ems should be connected or just a single device
        if ems_gcp_id is not None and ems_gcp_id != "":
            # save the corresponding ems
            ems_ent, ems_ent_dict = get_entity_by_id_from_dict_list(
                e_dict_list=dict_entities, e_id=ems_gcp_id
            )

            # connect the ems power values to the gcp
            world.connect(ems_ent, gcp, *model_connect_config[ems_ent_dict["type"]]["grid_load"])
            _logger.info(f"EMS '{ems_ent.eid}' connected to grid at {gcp.eid}.")

            # connect the grid ems to the ems
            if grid_ems_present:
                # Try to world connect gridemsent emsent modelconnectconfig GridEMS emsentdict type
                _logger.info(f"Grid EMS '{grid_ems_ent.eid}' connected to ems {ems_ent.eid}.")

            # add ems at this gcp to the entity dict
            dict_ent_gcp[ems_ent.type] = [ems_ent]

        else:  # no ems should be connected
            bool_gcp_connected = False

            # connect devices to the gcp, if possible
            for ent_type, ent_list in dict_ent_gcp.items():
                for ent in ent_list:
                    if "grid_load" not in model_connect_config[ent_type]:
                        # some devices are not directly connected to the grid, like electric vehicle
                        _logger.info(
                            f"Model Entity '{ent.eid}' not connected to grid - Connection"
                            " attributes missing in model_connect_config. (INFO: EV should be fine)"
                        )
                    else:
                        # check that it is not connected otherwise
                        if bool_gcp_connected:
                            _logger.error(f"{gcp.eid} cannot have two separate connections.")
                            raise KeyError(f"{gcp.eid} cannot have two separate connections.")

                        # connect device to gcp
                        world.connect(ent, gcp, *model_connect_config[ent.type]["grid_load"])
                        _logger.info(f"Entity '{ent.eid}' connected to grid at {gcp.eid}.")
                        bool_gcp_connected = True

                        # connect the grid ems to the device
                        if grid_ems_present:
                            # Try to world connect gridemsent ent modelconnectconfig GridEMS enttype
                            _logger.info(
                                f"Grid EMS '{grid_ems_ent.eid}' connected to entity {ent.eid}."
                            )

            # check that grid load is connected
            if not bool_gcp_connected:
                _logger.warn(f"No entity connected to grid at {gcp.eid}.")

        # connect all devices at (behind) this gcp
        connect_entities(world, dict_ent_gcp, model_connect_config, dict_simulators)


def connect_entities_to_db(sim_config: dict, world: object, database: object, dict_entities: dict):
    """Connects all models (model entities) to the database.

    Args:
        sim_config (dict): Information about the used simulators and their models
        world (object): mosaik world object to orchestrate the simulation process
        database (object): model object of the database for the simulation
        dict_entities (dict): dict of all used model entity objects
    """

    # connect all models given in sim_config simulator lists
    for sim_dict in sim_config.values():
        for model_name, model_output_properties in sim_dict["models"].items():
            # if hems is connected, check for correct model name (operating strategy)
            if model_name == "ems":
                ems_model_list = [
                    name for name in dict_entities.keys() if ("hems" in name or "HEMS" in name)
                ]
                for ems_name in ems_model_list:
                    mosaik.util.connect_many_to_one(
                        world, dict_entities[ems_name], database, *model_output_properties
                    )
            else:
                mosaik.util.connect_many_to_one(
                    world, dict_entities[model_name], database, *model_output_properties
                )

            _logger.info(f"Models of {model_name} connected to database.")


def connect_grid_to_db(sim_config_grid: dict, world: object, database: object, dict_comps: dict):
    """Connects all grid components to the database.

    Args:
        sim_config_grid (dict): Information about the used grid simulator and the components with a
            list of their output attributes
        world (object): mosaik world object to orchestrate the simulation process
        database (object): model object of the database for the simulation
        dict_comps (dict): dict of all used grid component entity objects, sorted by their type
    """

    for comp_name, comp_attr_list in sim_config_grid["components"].items():
        mosaik.util.connect_many_to_one(world, dict_comps[comp_name], database, *comp_attr_list)

        _logger.info(f"Grid components of type '{comp_name}' connected to database.")


def connect_to_forecast(
    world: object,
    dict_entities: dict,
    dict_simulators: dict,
    forecast: object,
    forecast_sim: object,
):
    """Create connections for the forecasts to work.
    Includes mosaik connections to ems model and adding of the model entities to the forecasts list.

    Args:
        world (object): mosaik world object to orchestrate the simulation process
        dict_entities (dict): dict of all used model entity objects
        dict_simulators (dict): dict of all used simulators with their ModelFactory-objects
        forecast (object): forecast model entity
        forecast_sim (object): simulator for the forecast model
    """

    # create connections for each entity of each model type
    for model_name, ent_list in dict_entities.items():
        for entity in ent_list:
            # for ems create connections to forecast entity
            if "ems" in model_name.lower():
                world.connect(entity, forecast, "forecast_request")
                world.connect(
                    forecast,
                    entity,
                    "forecast",
                    weak=True,
                    initial_data={"forecast": {forecast.full_id: {}}},
                )
            # for other models (devices) add those entities to the forecast entity list
            else:
                forecast_sim.add_forecasted_entity(
                    forecast.eid,
                    {entity.full_id: dict_simulators[model_name].get_entity_by_id(entity.eid)},
                )


def connect_entities_of_two_model_types(
    world: object,
    entity_list_strong: object,
    entity_list_weak: object,
    model_connect_config_from_strong: list,
    model_connect_config_from_weak: list = [],
    sim_entities_weak: object = None,
):
    """Connect the elements of two lists in both directions (if needed) via mosaik.
    Also add elements to list of controlled entities if the "weak" entity is an ems.

    Args:
        world (object): mosaik World object
        entity_list_strong (object): list of entities that have "strong" outgoing connections
        entity_list_weak (object): list of entities that have "weak" outgoing connections
        model_connect_config_from_strong (list): list of properties (str or tuple) to connect the
            two models types - from strong to weak
        model_connect_config_from_weak (list): list of properties (str or tuple) to connect the
            two models types - from weak to strong. Defaults to [].
        sim_entities_weak (object): Simulator of the "weak" entities for the adding of entities to
            the ems controlled entities. Defaults to None.

    Raises:
        TypeError: if given mosaik world is not correct (does not have connect method)
        ValueError: if no strong connection properties are given but there are weak connections
    """
    # check if world is correct mosaik:World object
    if not hasattr(world, "connect"):
        raise TypeError("world is not a correct mosaik:World object")

    # check connection configurations for both directions
    check_model_connect_config(model_connect_config_from_strong)
    check_model_connect_config(model_connect_config_from_weak)
    if model_connect_config_from_strong == []:  # check if given list is empty
        if model_connect_config_from_weak != []:
            raise ValueError("Not possible to give weak but no strong connections!")
        else:
            return  # no connections to be made for these models

    # go by each combination of entities in both directions
    for ent_strong in entity_list_strong:
        for ent_weak in entity_list_weak:
            # execute mosaik connect for strong connections
            world.connect(ent_strong, ent_weak, *model_connect_config_from_strong, weak=False)

            # execute mosaik connect for weak connections if needed
            if model_connect_config_from_weak is not None and model_connect_config_from_weak != []:
                # set initial data for weak connections
                dict_init_data = {}
                for conn_elem in model_connect_config_from_weak:
                    # set output values to zero for all outgoing connections to all entities
                    dict_elem = {
                        ent_strong_single.full_id: 0 for ent_strong_single in entity_list_strong
                    }
                    if isinstance(conn_elem, str):
                        dict_init_data[conn_elem] = dict_elem
                    elif isinstance(conn_elem, tuple):
                        dict_init_data[conn_elem[0]] = dict_elem

                # execute connect command for weak connection via mosaik
                world.connect(
                    ent_weak,
                    ent_strong,
                    *model_connect_config_from_weak,
                    weak=True,
                    initial_data=dict_init_data,
                )

            # if recieving entity is an energy management system: add transmitting entity to list
            if ent_weak.sim_name == "EMSSim" and sim_entities_weak is not None:
                entity, entity_dict = get_entity_by_id(e_list=[ent_strong], e_id=ent_strong.eid)
                sim_entities_weak.add_controlled_entity(ent_weak.eid, {entity.eid: entity_dict})

    _logger.info(f"Added connections between {ent_strong.type} and {ent_weak.type}.")


def get_default_dirs(
    dir_base,
    scenario: str = "building",
    grid: str = "example_grid_kerber.json",
    format_db: str = "hdf5",
) -> dict:
    """Gathers all needed directories resp. its paths based on eELib's default structure.

    Args:
        dir_base (str): string with path to root director
        scenario (str): Type of used scenario (like building, grid etc.). Defaults to "building".
        grid (str): name of the grid file to use. Defaults to "example_grid_kerber.json".
        format_db (str): format of the database. Defaults to None.

    Raises:
        FileNotFoundError: If model data for current simulation scenario not found

    Returns:
        dict: all relevant paths for a simulation
    """

    directory = {}

    directory["DATA"] = os.path.join(dir_base, "data")

    directory["RESULTS"] = os.path.join(directory["DATA"], "results")
    if not os.path.exists(directory["RESULTS"]):  # create result directory if necessary
        os.makedirs(directory["RESULTS"])

    directory["GRAPHS"] = os.path.join(directory["RESULTS"], "sim_graphs")
    if not os.path.exists(directory["GRAPHS"]):  # create graph directory if necessary
        os.makedirs(directory["GRAPHS"])

    directory["MODEL_DATA"] = os.path.join(
        directory["DATA"], "model_data_scenario", "model_data_" + scenario + ".json"
    )
    if not os.path.isfile(directory["MODEL_DATA"]):  # check if MODEL_DATA is valid
        raise FileNotFoundError("Model data for scenario not found!")

    if grid is not None:
        directory["GRID_DATA"] = os.path.join(directory["DATA"], "grid", grid)
        if not os.path.isfile(directory["GRID_DATA"]):  # check if GRID_DATA is valid
            raise FileNotFoundError("Grid data for grid scenario not found!")
        directory["MODEL_GRID_DATA"] = os.path.join(
            directory["DATA"], "grid", "grid_model_config.json"
        )
        if not os.path.isfile(
            directory["MODEL_GRID_DATA"]
        ):  # check if DIR_MODEL_GRID_DATA is valid
            raise FileNotFoundError("Data to grid-model-connection for grid scenario not found!")

    db_format = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    directory["DATABASE_FILENAME"] = os.path.join(
        directory["RESULTS"], ("results_{}." + format_db).format(db_format)
    )

    return directory
