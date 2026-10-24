INSERT INTO sdgs (sdg_id, name) VALUES
(1,'No Poverty'),(2,'Zero Hunger'),(3,'Good Health and Well-being'),(4,'Quality Education'),
(5,'Gender Equality'),(6,'Clean Water and Sanitation'),(7,'Affordable and Clean Energy'),
(8,'Decent Work and Economic Growth'),(9,'Industry, Innovation and Infrastructure'),
(10,'Reduced Inequalities'),(11,'Sustainable Cities and Communities'),
(12,'Responsible Consumption and Production'),(13,'Climate Action'),(14,'Life Below Water'),
(15,'Life on Land'),(16,'Peace, Justice and Strong Institutions'),(17,'Partnerships for the Goals');

INSERT INTO scenarios (name, description, demand_multiplier, automation_multiplier) VALUES
('Slow adoption','AI diffuses slowly; regulation and cost limit uptake',0.6,0.5),
('Moderate adoption','Current adoption trend continues',1.0,1.0),
('Fast disruption','Rapid capability gains and wide deployment',1.6,1.8);
