-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Create incidents table
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    incident_type VARCHAR(50) NOT NULL,
    severity INTEGER NOT NULL CHECK (severity BETWEEN 1 AND 5),
    location GEOMETRY(Point, 4326) NOT NULL,
    address VARCHAR(200),
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    description TEXT,
    affected_people INTEGER
);

-- Create resources table
CREATE TABLE IF NOT EXISTS resources (
    id SERIAL PRIMARY KEY,
    resource_type VARCHAR(50) NOT NULL,
    current_location GEOMETRY(Point, 4326) NOT NULL,
    status VARCHAR(20) DEFAULT 'available',
    capacity INTEGER,
    details JSONB
);

-- Create resource allocations table
CREATE TABLE IF NOT EXISTS resource_allocations (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents(id),
    resource_id INTEGER REFERENCES resources(id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estimated_arrival TIMESTAMP,
    actual_arrival TIMESTAMP,
    route GEOMETRY(LineString, 4326)
);

-- Create spatial indexes
CREATE INDEX idx_incidents_location ON incidents USING GIST(location);
CREATE INDEX idx_resources_location ON resources USING GIST(current_location);
CREATE INDEX idx_resource_allocations_route ON resource_allocations USING GIST(route);

-- Create function to find nearest resources
CREATE OR REPLACE FUNCTION find_nearest_resources(
    incident_point GEOMETRY,
    resource_type TEXT DEFAULT NULL,
    max_distance_km FLOAT DEFAULT 50,
    limit_count INTEGER DEFAULT 5
)
RETURNS TABLE(
    resource_id INTEGER,
    distance_km FLOAT,
    resource_type TEXT,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        ST_Distance(r.current_location::geography, incident_point::geography) / 1000 as distance_km,
        r.resource_type,
        r.status
    FROM resources r
    WHERE 
        (resource_type IS NULL OR r.resource_type = resource_type)
        AND ST_DWithin(r.current_location::geography, incident_point::geography, max_distance_km * 1000)
        AND r.status = 'available'
    ORDER BY r.current_location <-> incident_point
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Insert sample data
INSERT INTO incidents (incident_type, severity, location, address) VALUES
('fire', 4, ST_SetSRID(ST_MakePoint(77.2090, 28.6139), 4326), 'Central Delhi'),
('medical', 3, ST_SetSRID(ST_MakePoint(77.2190, 28.6239), 4326), 'East Delhi');

INSERT INTO resources (resource_type, current_location, status, capacity) VALUES
('ambulance', ST_SetSRID(ST_MakePoint(77.1990, 28.6039), 4326), 'available', 4),
('fire_truck', ST_SetSRID(ST_MakePoint(77.2290, 28.6339), 4326), 'available', 6),
('police', ST_SetSRID(ST_MakePoint(77.1890, 28.5939), 4326), 'available', 2);