#include "sailbot_db.h"

#include <bsoncxx/builder/stream/array.hpp>
#include <bsoncxx/builder/stream/document.hpp>
#include <bsoncxx/builder/stream/helpers.hpp>
#include <bsoncxx/json.hpp>
#include <cstdint>
#include <iostream>
#include <memory>
#include <mongocxx/client.hpp>
#include <mongocxx/collection.hpp>
#include <mongocxx/database.hpp>
#include <mongocxx/instance.hpp>

#include "sensors.pb.h"
#include "waypoint.pb.h"

namespace bstream = bsoncxx::builder::stream;
using Polaris::Sensors;

mongocxx::instance SailbotDB::inst_{};  // staticallly initialize instance so that it is available everywhere in this
                                        // translation unit
                                        // why is this not used anywhere else?

// PUBLIC

// constructor for a sailbotdb instance that takes in a db name to set, and a connection string that defines the port that
// is used on local host for now
SailbotDB::SailbotDB(const std::string & db_name, const std::string & mongodb_conn_str)
: db_name_(db_name)  // sets the db name
{
    mongocxx::uri uri = mongocxx::uri{
      // what exactly is uri ???
      mongodb_conn_str};  // creates a mongodb uri based on the connection string which is an address and port
    pool_ = std::make_unique<mongocxx::pool>(uri);  // given a database, create a set of ready to use connections
                                                    // that the app can connect to and access the db
}

// prints out a given document into the terminal, it prints out one set of data defined in the comments in sailbot_db.h
// converts the specific mongodb document into a JSON string and prints it out
void SailbotDB::printDoc(const DocVal & doc) { std::cout << bsoncxx::to_json(doc.view()) << std::endl; }

// tests the connection given
bool SailbotDB::testConnection()
{
    // creates the ping command using a bstream document???, command is the ping command to the DB
    const DocVal ping_cmd = bstream::document{} << "ping" << 1 << bstream::finalize;
    // acquire a connection to the db from one of the pools
    mongocxx::pool::entry entry = pool_->acquire();
    // obtain reference to the database from the connection
    mongocxx::database db = (*entry)[db_name_];
    try {
        // Ping the database.
        // apparently ping throws an exception if the ping command doesn't work and cant connect?
        db.run_command(ping_cmd.view());
        return true;
    } catch (const std::exception & e) {
        std::cerr << "Exception: " << e.what() << std::endl;
        return false;
    }
}

// given a sensors protobuf and iridium information, write to the db
// each message from iridium will contain the entire system data instead of just new ones
bool SailbotDB::storeNewSensors(const Sensors & sensors_pb, RcvdMsgInfo new_info)
{
    // Only using timestamp info for now, may use other fields in the future
    const std::string &   timestamp = new_info.timestamp_;
    mongocxx::pool::entry entry     = pool_->acquire();  // acquire connection to DB
    // store all data individually
    return storeGps(sensors_pb.gps(), timestamp, *entry) && storeAis(sensors_pb.ais_ships(), timestamp, *entry) &&
           storeGenericSensors(sensors_pb.data_sensors(), timestamp, *entry) &&
           storeBatteries(sensors_pb.batteries(), timestamp, *entry) &&
           storeWindSensors(sensors_pb.wind_sensors(), timestamp, *entry) &&
           storePathSensors(sensors_pb.local_path_data(), timestamp, *entry);
}

// END PUBLIC

// PRIVATE

// given a sensors::gps protobuf, the timestamp of message, and a mongodb client connected to DB, write gps data to db
bool SailbotDB::storeGps(const Sensors::Gps & gps_pb, const std::string & timestamp, mongocxx::client & client)
{
    // obtain reference to DB
    mongocxx::database db = client[db_name_];
    // obtain reference to the gps collection
    mongocxx::collection gps_coll = db[COLLECTION_GPS];
    // create new document entry to the DB given the latitude, longitude, speed, and heading
    DocVal gps_doc = bstream::document{} << "latitude" << gps_pb.latitude() << "longitude" << gps_pb.longitude()
                                         << "speed" << gps_pb.speed() << "heading" << gps_pb.heading() << "timestamp"
                                         << timestamp << bstream::finalize;

    // insert the document entry to the DB and return the status
    return static_cast<bool>(gps_coll.insert_one(gps_doc.view()));
}

// given a sensors::ais protobuf, the timestamp of message, and mongodb client connected to DB, write AIS data to the db
bool SailbotDB::storeAis(
  const ProtoList<Sensors::Ais> & ais_ships_pb, const std::string & timestamp, mongocxx::client & client)
{
    // obtain reference to DB and correct collection
    mongocxx::database   db       = client[db_name_];
    mongocxx::collection ais_coll = db[COLLECTION_AIS_SHIPS];

    // since the ais protobuf contains an array of ships, need to create document differently
    bstream::document doc_builder{};
    // create an array named ships
    auto ais_ships_doc_arr = doc_builder << "ships" << bstream::open_array;
    for (const Sensors::Ais & ais_ship : ais_ships_pb) {
        // The BSON spec does not allow unsigned integers (throws exception), so cast our uint32s to sint64s
        // push ship data into the document array
        ais_ships_doc_arr = ais_ships_doc_arr
                            // creates a document entry for each boat
                            << bstream::open_document << "id" << static_cast<int64_t>(ais_ship.id()) << "latitude"
                            << ais_ship.latitude() << "longitude" << ais_ship.longitude() << "sog" << ais_ship.sog()
                            << "cog" << ais_ship.cog() << "rot" << ais_ship.rot() << "width" << ais_ship.width()
                            << "length" << ais_ship.length() << bstream::close_document;
    }
    // close the array, add a timestamp, and complete the document
    DocVal ais_ships_doc = ais_ships_doc_arr << bstream::close_array << "timestamp" << timestamp << bstream::finalize;
    // insert the document to the db
    return static_cast<bool>(ais_coll.insert_one(ais_ships_doc.view()));
}

// same as ais ships but for generic sensors
bool SailbotDB::storeGenericSensors(
  const ProtoList<Sensors::Generic> & generic_pb, const std::string & timestamp, mongocxx::client & client)
{
    mongocxx::database   db           = client[db_name_];
    mongocxx::collection generic_coll = db[COLLECTION_DATA_SENSORS];
    bstream::document    doc_builder{};
    auto                 generic_doc_arr = doc_builder << "genericSensors" << bstream::open_array;
    for (const Sensors::Generic & generic : generic_pb) {
        generic_doc_arr = generic_doc_arr << bstream::open_document << "id" << static_cast<int64_t>(generic.id())
                                          << "data" << static_cast<int64_t>(generic.data()) << bstream::close_document;
    }
    DocVal generic_doc = generic_doc_arr << bstream::close_array << "timestamp" << timestamp << bstream::finalize;
    return static_cast<bool>(generic_coll.insert_one(generic_doc.view()));
}

// same as ais ships but for batteries
bool SailbotDB::storeBatteries(
  const ProtoList<Sensors::Battery> & battery_pb, const std::string & timestamp, mongocxx::client & client)
{
    mongocxx::database   db             = client[db_name_];
    mongocxx::collection batteries_coll = db[COLLECTION_BATTERIES];
    bstream::document    doc_builder{};
    auto                 batteries_doc_arr = doc_builder << "batteries" << bstream::open_array;
    for (const Sensors::Battery & battery : battery_pb) {
        batteries_doc_arr = batteries_doc_arr << bstream::open_document << "voltage" << battery.voltage() << "current"
                                              << battery.current() << bstream::close_document;
    }
    DocVal batteries_doc = batteries_doc_arr << bstream::close_array << "timestamp" << timestamp << bstream::finalize;
    return static_cast<bool>(batteries_coll.insert_one(batteries_doc.view()));
}

// similar to ais ships but for wind sensors
bool SailbotDB::storeWindSensors(
  const ProtoList<Sensors::Wind> & wind_pb, const std::string & timestamp, mongocxx::client & client)
{
    mongocxx::database   db        = client[db_name_];
    mongocxx::collection wind_coll = db[COLLECTION_WIND_SENSORS];
    bstream::document    doc_builder{};
    auto                 wind_doc_arr = doc_builder << "windSensors" << bstream::open_array;
    for (const Sensors::Wind & wind_sensor : wind_pb) {
        wind_doc_arr = wind_doc_arr << bstream::open_document << "speed" << wind_sensor.speed() << "direction"
                                    << static_cast<int16_t>(wind_sensor.direction()) << bstream::close_document;
    }
    DocVal wind_doc = wind_doc_arr << bstream::close_array << "timestamp" << timestamp << bstream::finalize;
    return static_cast<bool>(wind_coll.insert_one(wind_doc.view()));
}

// same as ais ships but for path sensors
bool SailbotDB::storePathSensors(
  const Sensors::Path & local_path_pb, const std::string & timestamp, mongocxx::client & client)
{
    mongocxx::database           db              = client[db_name_];
    mongocxx::collection         local_path_coll = db[COLLECTION_LOCAL_PATH];
    bstream::document            doc_builder{};
    auto                         local_path_doc_arr = doc_builder << "waypoints" << bstream::open_array;
    ProtoList<Polaris::Waypoint> waypoints          = local_path_pb.waypoints();
    for (const Polaris::Waypoint & waypoint : waypoints) {
        local_path_doc_arr = local_path_doc_arr << bstream::open_document << "latitude" << waypoint.latitude()
                                                << "longitude" << waypoint.longitude() << bstream::close_document;
    }
    DocVal local_path_doc = local_path_doc_arr << bstream::close_array << "timestamp" << timestamp << bstream::finalize;
    return static_cast<bool>(local_path_coll.insert_one(local_path_doc.view()));
}

// END PRIVATE