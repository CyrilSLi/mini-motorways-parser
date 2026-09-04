# Built-in modules
import json, os
from datetime import datetime, timezone

# Third-party modules
from dotenv import load_dotenv

load_dotenv()


tile_direction_enum = ["North", "NorthEast", "East", "SouthEast", "South", "SouthWest", "West", "NorthWest", "None"] # -1 = None
road_type_enum = ["TwoLane", "Roundabout", "Motorway", "Driveway", "Carpark", "ParkingSpace"]
obstacle_type_enum = ["None", "Target", "LeadingVehicle", "BlockingIntersection", "HotswappingLane"]
pathfind_urgency_enum = ["NotRequired", "WhenPossible", "AsSoonAsPossible"]
behavior_state_enum = ["WaitingForDestination", "DrivingToDestination", "ParkingAtDestination", "ParkedAtDestination", "DrivingHome", "RealigningDriveway"]
road_state_dict = {0: "None", 2: "Planned", 4: "Pending", 8: "Active", 0x10: "Mothballed", 0x18: "Live", 0xE: "VisiblyActive", 0xC: "ActiveOrPending"}
tile_content_type_enum = ["None", "House", "Destination", "Carpark", "Tree", "BoatTerminal"]
destination_type_enum = ["Destination", "TrainStation", "BoatTerminal"]
tutorial_identifier_enum = ["None", "FirstHouse", "FirstDestination", "SecondColorHouse", "SecondColorDestination", "AwkwardDrivewayHouse", "LastHouseBeforeBridgeUpgrade", "HouseAcrossRiver", "SecondHouse", "DiagonalHouse", "ThirdColorDestination", "SetupTrafficLight_LastHouse", "HouseBeforePanTutorial", "SetupMotorway_LastHouse", "SetupRoundabout_LastHouse", "LastHouseBeforeBigPin", "BigPinDestination", "SetupTrafficLight_FirstHouse", "SetupMotorway_FirstHouse", "SetupRoundabout_FirstHouse", "UpgradeMotorway_Destination", "GameOverDestination", "SetupTrafficLight_SecondHouse"]
upgrade_type_enum = ["Concrete", "Bridge", "Motorway", "TrafficLight", "Roundabout", "Tunnel", "House", "Destination", "DoubleDestination", "Count"]
disabled_upgrade_options_dict = {0: "None", 2: "Option1", 4: "Option2", 8: "Option3", 0x10: "Option4", 0x20: "Option5", 0x40: "Option6"}
building_spawning_mode_enum = ["None", "Houses", "Destinations", "All"]
city_tile_type_enum = ["Demand", "Supply"]
carpark_preference_enum = ["NoPreference", "Solo", "ForceDouble", "Double", "JoinDouble", "Station", "JoinStation", "ForceNewDouble", "ForceNewStation", "ForceNewBoatTerminal", "JoinBoatTerminal"]
grouping_style_enum = ["Normal", "Near", "Far", "Circle"]
carpark_entrance_enum = ["TopLeft", "BottomRight", "TopLeftAndBottomRight"]
demand_generation_style_enum = ["Timer", "PermanentBalanced"]





def read_int(length):
    return int.from_bytes(f.read(length), byteorder="little", signed=True)

def read_int32():
    return read_int(4)

def read_vlq():
    value = 0
    shift = 0
    while True:
        byte = f.read(1)
        if not byte:
            raise EOFError("Unexpected end of file while reading VLQ")
        byte = ord(byte)
        value |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
    return value

def read_string():
    length = read_vlq()
    return f.read(length).decode("utf-8")

def read_bool():
    return bool(read_int(1))

def read_format_hex(length):
    hex_str = f.read(length).hex().upper()
    return " ".join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))

def read_timestamp():
    timestamp = int.from_bytes(f.read(8), byteorder="little", signed=True)
    kind = (timestamp >> 62) & 0x03
    ticks = timestamp & 0x3FFFFFFFFFFFFFFF

    posix_sec = (ticks / 10_000_000) - 62135596800
    if kind == 1:
        dt = datetime.fromtimestamp(posix_sec, tz=timezone.utc)
    else:
        dt = datetime.fromtimestamp(posix_sec)
    return dt

def read_timestamp_seconds():
    return datetime.fromtimestamp(read_int32(), tz=timezone.utc)

def read_fix64():
    return int.from_bytes(f.read(8), byteorder="little", signed=True) / (1 << 32)

def read_object():
    return {
        "$ref": f"#/{read_int32()}"
    }

def read_vector2fixed():
    return (read_fix64(), read_fix64())

def read_vector3fixed():
    return (read_fix64(), read_fix64(), read_fix64())

def read_vector2int():
    return (read_int32(), read_int32())

def read_vector3int():
    return (read_int32(), read_int32(), read_int32())

def read_list(read_element):
    list_length = read_int32()
    if list_length == -1:
        return []
    return [read_element() for _ in range(list_length)]

def read_array(read_element):
    array_length = read_int32()
    if array_length == 0: # Different from read_list
        return []
    return [read_element() for _ in range(array_length)]

def read_dict(read_key, read_value):
    dict_length = read_int32()
    if dict_length == 0:
        return {}
    return {read_key(): read_value() for _ in range(dict_length)}



# Readers for specific data structures




def read_corneradjacencyreference():
    return (read_int32(), read_int32(), tile_direction_enum[read_int32()])

def read_roadtileconnection():
    has_motorway_nodes = read_bool()
    rtc = {
        "input_direction": tile_direction_enum[read_int(1)],
        "input_type": road_type_enum[read_int(1)],
        "input_motorway_id": read_int32() if has_motorway_nodes else None,
        "output_direction": tile_direction_enum[read_int(1)],
        "output_type": road_type_enum[read_int(1)],
        "output_motorway_id": read_int32() if has_motorway_nodes else None
    }
    return rtc

def read_railtileconnection():
    rtc = {
        "input_direction": tile_direction_enum[read_int(1)],
        "output_direction": tile_direction_enum[read_int(1)]
    }
    return rtc

def read_boatpathtileconnection():
    bptc = {
        "input_direction": tile_direction_enum[read_int(1)],
        "output_direction": tile_direction_enum[read_int(1)]
    }
    return bptc

def read_tiledirectionbitfield():
    bitfield = read_int32()
    directions = []
    for i in range(8):
        if bitfield & (1 << i):
            directions.append(tile_direction_enum[i])
    return directions

def read_upgradepackagedefinition():
    upd = {
        "type": upgrade_type_enum[read_int32()],
        "amount": read_int32(),
        "additional_concrete": read_int32()
    }
    return upd

def read_upgradechoice():
    uc = {
        "choices": read_list(read_upgradepackagedefinition),
        "is_free": read_bool(),
        "disabled_options": []
    }
    disabled_options_bitfield = read_int32()
    for (k, v) in disabled_upgrade_options_dict.items():
        if disabled_options_bitfield & k:
            uc["disabled_options"].append(v)
    return uc

def read_vehicledispatchrecord():
    vdr = {
        "simulation_frame": read_int32(),
        "house_coordinates": read_vector2int(),
        "destination_coordinates": read_vector2int(),
    }
    return vdr

def read_scheduledbuilding():
    sb = {
        "time": read_fix64(),
        "spawn_attempts": read_int32(),
        "type": city_tile_type_enum[read_int32()],
        "group_index": read_int32(),
        "carpark_preference": carpark_preference_enum[read_int32()],
        "grouping": grouping_style_enum[read_int32()],
        "demand_multiplier": read_fix64(),
        "initial_upgrade_level": read_int32(),
        "use_fixed_parameters": read_bool(),
        "position_override": read_vector2int(),
        "entrance_override": carpark_entrance_enum[read_int32()],
        "driveway_direction_override": tile_direction_enum[read_int32()],
        "carpark_side_override": tile_direction_enum[read_int32()],
        "tutorial_identifier": tutorial_identifier_enum[read_int32()],
    }
    return sb

def read_challengedata():
    cd = {
        "name": read_string(),
    }
    return cd

def read_passage():
    p = {
        "upgrade_type": upgrade_type_enum[read_int32()],
        "is_complete": read_bool(),
        "start_coordinates": read_vector2int(),
        "end_coordinates": read_vector2int(),
        "crossing_coordinates": read_list(read_vector2int),
    }
    return p



# Readers for specific models

def read_simulation():
    s = {
        "models": read_dict(lambda: read_format_hex(4), lambda: read_list(read_object)), # Dictionary<Type, IModel>
        "unknown": read_list(read_object), # TODO: Determine what this field represents
        "unknown2": read_format_hex(18), # TODO: Determine what this field represents
    }
    return s

def read_clock():
    c = {
        "time": read_fix64(),
    }
    return c

def read_commandjournal():
    cj = {
        "unknown": read_format_hex(4), # TODO: Determine what this field represents
    }
    return cj

def read_tutorialprogressionprocess():
    return {}

def read_dispatchvehiclesprocess():
    dvp = {
        # "sorted_destinations_with_demand": read_array(read_object) # List of DestinationModel
        "unknown": read_format_hex(140), # TODO: Determine what this field represents
    }
    return dvp

def read_generatedemandprocess():
    gdp = {
        "demand_generation_style": demand_generation_style_enum[read_int(1)],
        "allocated_color_groups": read_array(read_bool)
    }
    return gdp

def read_laneupdateprocess():
    lup = {
        "city_model": read_object(), # CityModel
    }
    return lup

def read_citymodel():
    cm = {
        "city_name": read_string(),
        "pseudorandomgenerator": read_object(),
        "start_offset": read_vector3fixed(),
        "latest_lane_change_frame": read_int32(),
        "mode": mode_enum[read_int32()],
        "initial_mode": mode_enum[read_int32()]
    }
    return cm

def read_pseudorandomgenerator():
    prg = {
        "seed": read_format_hex(16)
    }
    return prg

def read_passagemodel():
    pm = {
        "passage": read_object(), # Passage
    }
    return pm

def read_tilecornermodel():
    tcm = {
        "adjacency_references": read_array(read_corneradjacencyreference),
        "world_position": read_vector2fixed(),
        "road_chunk": read_object(), # RoadChunkModel
    }
    return tcm

def read_vehiclemodel():
    vm = {
        "last_attempted_pathfind_frame": read_int32(),
        "house": read_object(), # HouseModel
        "destination": read_object(), # DestinationModel
        "last_visited_destination": read_object(), # DestinationModel
        "behavior_state": behavior_state_enum[read_int32()],
        "last_notified_behavior_state": behavior_state_enum[read_int32()],
        "path": read_list(read_object), # List of LaneModel
        "repath_urgency": pathfind_urgency_enum[read_int32()],
        "target_distance_along_last_lane": read_fix64(),
        "path_length": read_fix64(),
        "path_length_at_start_of_journey": read_fix64(),
        "is_shoving_into_next_intersection": read_bool(),
        "vehicle_pushing_into": read_object(), # VehicleModel
        "time_when_arrived_at_house": read_fix64(),
        "return_path": read_list(read_object), # List of LaneModel
        "return_repath_urgency": pathfind_urgency_enum[read_int32()],

        "lane": read_object(), # LaneModel
        "distance_along_lane": read_fix64(),
        "speed": read_fix64(),
        "acceleration": read_fix64(),
        "nearest_obstacle": obstacle_type_enum[read_int32()],
        "leading_vehicle": read_object(), # VehicleModel
        "distance_to_leading_vehicle": read_fix64(),
        "blocking_lane": read_object(), # LaneModel
        "distance_to_blocking_lane": read_fix64(),
    }
    return vm

def read_lanemodel():
    lm = {
        "is_endpoint_lane": read_bool(),
        "is_carpark_lane": read_bool(),
        "has_been_used": read_bool(),
        "bespoke_lane_points": read_list(read_vector2fixed),
        "unknown": read_format_hex(4),                                   # TODO: Determine what this field represents
        "world_offset": read_vector2fixed(),
        "connection": read_roadtileconnection(),
        "road_state": road_state_dict[read_int32()],
        "is_temporary": read_bool(),
        "outbound_lanes": read_list(read_object), # List of LaneModel
        "road_chunk": read_object(), # RoadChunkModel
        "vehicles": read_list(read_object), # List of VehicleModel
    }
    return lm

def read_roadchunkmodel():
    rcm = {
        "lanes": read_list(read_object), # List of LaneModel
        "lane_speed_limit_scale": read_fix64(),
        "is_tile_corner": read_bool(),
        "traffic_light_model": read_object(), # TrafficLightModel
        "inbound_vehicles": read_list(read_object), # List of InboundVehicle
        "returning_inbound_vehicles": read_list(read_object), # List of InboundVehicle
        "outbound_directions": read_tiledirectionbitfield(),
        "train_crossing_model": read_object(), # TrainCrossingModel
    }
    return rcm

def read_inboundvehicle():
    iv = {
        "vehicle": read_object(), # VehicleModel
        "chosen_lane": read_object(), # LaneModel
        "timestamp": read_fix64(),
        "committed_timestamp": read_fix64(),
        # "is_shoving": read_bool(),
    }
    return iv

def read_housemodel():
    hm = {
        "group_index": read_int32(),
        "waiting_vehicles": read_list(read_object), # List of VehicleModel
        "realigning_vehicles": read_list(read_object), # List of VehicleModel
        "owned_vehicles": read_list(read_object), # List of VehicleModel
        "tile_model": read_object(), # TileModel
    }
    return hm

def read_tilemodel():
    tm = {
        "tile": read_object(), # Tile
        "world_position": read_vector2fixed(),
        "road_chunk": read_object(), # RoadChunkModel
        "rail_tile_model": read_object(), # RailTileModel
        "boat_path_tile_model": read_object(), # BoatPathTileModel
    }
    return tm

def read_tile():
    t = {
        "has_traffic_light": read_bool(),
        "traffic_light_permanence_progress": read_fix64(),
        "rail_tile_connection": read_railtileconnection(),
        "boat_path_tile_connection": read_boatpathtileconnection(),
        "is_center_of_roundabout": read_bool(),
        "roundabout_permanence_progress": read_fix64(),
        "two_lane_road_state": [road_state_dict[i] for i in read_array(read_int32)],
        "unbuilt_motorway_id": read_int32(),
        "unbuilt_motorway_number": read_int32(),
        "planned_roudabout_input": tile_direction_enum[read_int32()],
        "planned_roudabout_output": tile_direction_enum[read_int32()],
        "active_roundabout_input": tile_direction_enum[read_int32()],
        "active_roundabout_output": tile_direction_enum[read_int32()],
        "mothballed_roundabout_input": tile_direction_enum[read_int32()],
        "mothballed_roundabout_output": tile_direction_enum[read_int32()],
        "planned_motorways": read_array(read_int32),
        "active_motorways": read_array(read_int32),
        "mothballed_motorways": read_array(read_int32),
        "is_direction_immutable": read_tiledirectionbitfield(),
        "node_permanance_progress": read_array(read_fix64),
        "tilemap": read_object(), # ITilemap
        "coordinates": read_vector2int(),
        "content_type": tile_content_type_enum[read_int32()],
        "content_model": read_object(), # IModel
    }
    return t

def read_tilemapmodel():
    tmm = {
        "tiles": read_dict(read_vector2int, read_object), # Dictionary<Vector2Int, TileModel>
        "tile_corners": read_dict(read_corneradjacencyreference, read_object), # Dictionary<CornerAdjacencyReference, TileCornerModel>
        "temporary_lanes": read_list(read_object), # List of LaneModel
        "motorways": read_dict(read_int, read_object), # Dictionary<int, MotorwayModel>
    }
    return tmm

def read_destinationmodel():
    dm = {
        "destination_type": destination_type_enum[read_int32()],
        "group_index": read_int32(),
        "closest_rail_tile": read_object(), # RailTileModel
        "is_active": read_bool(),
        "demand_multiplier": read_fix64(),
        "demand_timer": read_fix64(),
        "demand_level_up_time": read_fix64(),
        "unassigned_demand": read_list(read_int32),
        "waiting_demand": read_list(read_int32),
        "contributed_supply": read_fix64(),
        "total_serviced_pins": read_int32(),
        # "activation_time": read_fix64(),
        "tile_models": read_list(read_object), # List of TileModel
        "carpark": read_object(), # CarparkModel
        # "tutorial_identifier": tutorial_identifier_enum[read_int32()],

        "overcrowding_time": read_fix64(),
        "overcrowding_speed": read_fix64(),
    }
    return dm

def read_carparkmodel():
    cpm = {
        "origin": read_vector2int(),
        "carpark_side": tile_direction_enum[read_int32()],
        "footprint": read_vector2int(),
        "entrance_at_top_left": read_bool(),
        "entrance_at_bottom_right": read_bool(),
        "supports_boats": read_bool(),
        "carpark_tiles": read_list(read_vector2int),
        "destination_offsets": read_list(read_vector2int),
        "entrance_lanes": read_list(read_object), # List of LaneModel
        "spaces": read_list(read_object), # List of ParkingSpace
        "vehicles_entering": read_list(read_object), # List of VehicleModel
        "vehicles_driving_through": read_list(read_object), # List of VehicleModel
        "destinations": read_list(read_object), # List of DestinationModel
        "tile_models": read_list(read_object), # List of TileModel
    }
    return cpm

def read_parkingspace():
    ps = {
        "park_road_chunk": read_object(), # RoadChunkModel
        "inner_road_chunk": read_object(), # RoadChunkModel
        "outer_road_chunk": read_object(), # RoadChunkModel
        "vehicle": read_object(), # VehicleModel
        "time_vehicle_parked": read_fix64(),
    }
    return ps

def read_treemodel():
    tm = {
        "prefab_index": read_int32(),
        "tile_model": read_object(), # TileModel
    }
    return tm

def read_trafficlightmodel():
    tlm = {
        "duration_on_current_pair": read_fix64(),
        "current_pair_index": read_int32(),
        "green_light_pairs": read_list(read_tiledirectionbitfield),
        "owning_chunk": read_object(), # RoadChunkModel
        "requires_pair_calculation": read_bool(),
        "is_in_overtime": read_bool(),
        "amber_lights_on": read_bool(),
    }
    return tlm

def read_gamebehaviourmodel():
    gbm = {
        "can_game_over": read_bool(),
    }
    return gbm

def read_activechallengesmodel():
    acm = {
        "challenges": read_list(read_challengedata),
        "challenge_type": challenge_type_enum[read_int32()],
        "city_challenge_index": read_int32(),
        "time_end": read_timestamp_seconds(),
        "time_start": read_timestamp_seconds(),
        "initial_seed": read_int(8),
    }
    return acm

def read_upgradedatabasemodel():
    udm = {
        "claimed_package_counts": read_array(read_int32),
        "consecutive_weeks_since_upgrade_last_presented": read_array(read_int32),
        "pending_upgrade_choices": read_list(read_upgradechoice),
        "num_choices_made": read_int32(),
        "accumulated_upgrade_schedule_delay_time": read_fix64(),
        "upgrade_schedule_passed": read_bool(),
        #"total_claimed_packages": read_int32(),
        # "last_claimed_package_type": upgrade_type_enum[read_int32()],
    }
    for _ in range(3):
        read_array(read_int32) # UNKNOWN
    read_int32() # UNKNOWN
    read_int32() # UNKNOWN
    for _ in range(3):
        read_array(read_int32) # UNKNOWN
    return udm

def read_snapshotmodel():
    sm = {
        "vehicle_dispatches": read_list(read_vehicledispatchrecord)
    }
    return sm

def read_scoremodel():
    sm = {
        "score": read_int32(),
        "efficiency_score": read_fix64(),
        "current_efficiency_milestone": read_int32(),
    }
    return sm

def read_clockmodel():
    cm = {
        "is_paused": read_bool(),
        "expansion_time_manually_paused": read_bool(),

        "time": read_fix64(),
        "expansion_time": read_fix64(),
    }
    return cm

def read_demandmodel():
    dm = {
        "spawn_scale": read_fix64(),
        "does_supply_need_recalculation": read_bool(),
        "supply_scales": read_dict(read_int32, read_fix64),
        "demand_oscillation_offsets": read_dict(read_int32, read_fix64),
        "extra_demand": read_dict(read_int32, read_fix64),
    }
    return dm

def read_cityplanmodel():
    cpm = {
        "scheduled_buildings": read_list(read_scheduledbuilding),
        "latest_house_spawn_time": read_dict(read_int32, read_fix64),
        "group_house_counts": read_array(read_int32),
        "suburb_count": read_dict(read_int32, read_int32),
        "nearby_house_count_of_group": read_dict(read_int32, read_object), # Dictionary<int, TileMatrixInt>
        "distance_to_nearest_house_of_group": read_dict(read_int32, read_object), # Dictionary<int, TileMatrixInt>
        "distance_to_nearest_destination_of_group": read_dict(read_int32, read_object), # Dictionary<int, TileMatrixInt>
        "destination_lanes": read_list(read_object), # List of LaneModel
        "spawning_mode": building_spawning_mode_enum[read_int32()],
        "double_destination_probability": read_fix64(),
    }
    return cpm

def read_tilematrixint():
    tmi = {
        "x": read_int32(),
        "y": read_int32(),
        "width": read_int32(),
        "height": read_int32(),
        "array_size": read_int32()
    }
    assert tmi['array_size'] == tmi['width'] * tmi['height'], f"Array size mismatch: {tmi['array_size']} != {tmi['width']} * {tmi['height']}"

    matrix = []
    for row in range(tmi["height"]):
        matrix.append([read_int32() for _ in range(tmi["width"])])
    tmi["matrix"] = list(reversed(matrix))

    read_int32() # UNKNOWN

    return tmi



f = open(os.getenv("GAME_JOURNAL_PATH"), "rb")

with open("type_ids.txt", "r") as f_types:
    type_ids = {int(line[0]): line[1] for line in map(str.split, f_types.read().splitlines())}


if True: # Header
    preamble = read_format_hex(32)
    print(f"Preamble: {preamble}")

    motive_enum = ["Autosave", "DiagnosticsReport", "PlayerQuit", "AppDeactivated"]
    motive = motive_enum[read_int32()]
    print(f"Motive: {motive}")

    device_model = read_string()
    print(f"Device Model: {device_model}")

    device_name = read_string()
    print(f"Device Name: {device_name}")

    timestamp = read_timestamp()
    print(f"Timestamp: {timestamp.astimezone().strftime("%B %d, %Y %H:%M:%S")}")

    assembler_hash = read_format_hex(4)
    print(f"Assembler Hash: {assembler_hash}")

    city_id = read_string()
    print(f"City ID: {city_id}")

    mode_enum = ["Normal", "Tutorial", "Background", "Endless", "Expert", "Movie", "Cinematic", "Creative"]
    mode = mode_enum[read_int32()]
    print(f"Mode: {mode}")

    trip_count = read_int32()
    print(f"Trip Count: {trip_count}")

    time_elapsed = read_fix64()
    print(f"Time Elapsed: {time_elapsed:.2f} seconds")

    challenge_type_enum = ["None", "Daily", "Weekly", "Mystery", "City"]
    challenge_type = challenge_type_enum[read_int32()]
    print(f"Challenge Type: {challenge_type}")

    challenge_end_time = read_timestamp_seconds()
    if challenge_type != "None":
        print(f"Challenge End Time: {challenge_end_time.astimezone().strftime("%B %d, %Y %H:%M:%S")}")

    challenge_index = read_int32()
    if challenge_type != "None":
        print(f"Challenge Index: {challenge_index}")

    print(f"File Position: {f.tell()}")
print()

type_information = {}
if True: # Types
    export_size = read_int(8)
    print(f"Export Size: {export_size}")

    assembler_hash_2 = read_format_hex(4)
    assert assembler_hash == assembler_hash_2, "Assembler Hash mismatch"

    serializer_version = read_int32()
    print(f"Serializer Version: {serializer_version}")

    type_count = read_int32()
    print(f"Type Count: {type_count}")

    for i in range(type_count):
        type_id = read_int32()
        type_serializer_hash = read_format_hex(4)
        object_count = read_int32()
        if type_serializer_hash == "01 00 00 00": # Skip types with serializer hash 01 00 00 00 (likely empty or placeholder types)
            print(f"Skipping Type {type_ids.get(type_id, type_id)}")
        else:
            print(f"Type {i:<5}ID: {type_ids.get(type_id, type_id)}, Serializer Hash: {type_serializer_hash}, Object Count: {object_count}")
        type_information[type_ids.get(type_id, type_id)] = {
            "serializer_hash": type_serializer_hash,
            "object_count": object_count
        }

    print(f"Meaningful Types: {len(type_information)}")
    print(f"File Position: {f.tell()}")
print()

models = {
    "Server.Simulation": read_simulation,
    "Server.Clock": read_clock,
    "Server.CommandJournal": read_commandjournal,
    "Motorways.Processes.TutorialProgressionProcess": read_tutorialprogressionprocess,
    "Motorways.Processes.DispatchVehiclesProcess": read_dispatchvehiclesprocess,
    "Motorways.Processes.GenerateDemandProcess": read_generatedemandprocess,
    "Motorways.Processes.LaneUpdateProcess": read_laneupdateprocess,
    "Motorways.Models.CityModel": read_citymodel,
    "PseudorandomGenerator": read_pseudorandomgenerator,
    "Motorways.Models.PassageModel": read_passagemodel,
    "Motorways.Passage": read_passage,
    "Motorways.Models.TrafficLightModel": read_trafficlightmodel,
    "Motorways.Models.RoadChunkModel": read_roadchunkmodel,
    "Motorways.Models.RoadChunkModel+InboundVehicle": read_inboundvehicle,
    "Motorways.Models.LaneModel": read_lanemodel,
    "Motorways.Models.VehicleModel": read_vehiclemodel,
    "Motorways.Models.HouseModel": read_housemodel,
    "Motorways.Models.TileModel": read_tilemodel,
    "Motorways.Tile": read_tile,
    "Motorways.Models.TilemapModel": read_tilemapmodel,
    "Motorways.Models.TileCornerModel": read_tilecornermodel,
    "Motorways.Models.CarparkModel": read_carparkmodel,
    "Motorways.Models.DestinationModel": read_destinationmodel,
    "Motorways.Models.CarparkModel+ParkingSpace": read_parkingspace,
    "Motorways.Models.TreeModel": read_treemodel,
    "Motorways.Models.GameBehaviourModel": read_gamebehaviourmodel,
    "Motorways.Models.ActiveChallengesModel": read_activechallengesmodel,
    "Motorways.Models.UpgradeDatabaseModel": read_upgradedatabasemodel,
    "Motorways.Models.SnapshotModel": read_snapshotmodel,
    "Motorways.Models.ScoreModel": read_scoremodel,
    "Motorways.Models.ClockModel": read_clockmodel,
    "Motorways.Models.DemandModel": read_demandmodel,
    "Motorways.Models.CityPlanModel": read_cityplanmodel,
    "Motorways.TileMatrixInt": read_tilematrixint,
    "VehicleDispatchRecord": read_vehicledispatchrecord,
}

game_data = [
    {
        "_id": 0,
        "_type": "_null"
    }
]
object_id = 0

for model in type_information:
    for i in range(type_information[model]["object_count"]):
        object_id += 1
        if type_information[model]["serializer_hash"] == "01 00 00 00":
            continue
        elif model not in models:
            print(f"Warning: No reader function defined for {model}")

        game_data.append({
            "_id": object_id,
            "_type": model,
            **models[model]()
        })
    print(f.tell(), model)
assert f.read(1) == b"", "File not fully read"



def stringify_keys(obj):
    if isinstance(obj, dict):
        return {json.dumps(k) if isinstance(k, tuple) else k: stringify_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [stringify_keys(i) for i in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

with open(".dev/game_data.json", "w") as f_out:
    json.dump({i.pop("_id"): i for i in stringify_keys(game_data)}, f_out, indent=4)
print("Game data written to .dev/game_data.json")


""" for j, i in enumerate(game_data["Motorways.TileMatrixInt"]):
    with open(f".dev/tm{j}.txt", "w") as f_out:
        for row in i["matrix"]:
            f_out.write("".join(f"{x:<12}" for x in row) + "\n") """