DROP TABLE IF EXISTS `user`;
DROP TABLE IF EXISTS `room`;
CREATE TABLE `user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `token` varchar(255) DEFAULT NULL,
  `leader_card_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`)
);

CREATE TABLE `room` (
  `room_id` bigint NOT NULL AUTO_INCREMENT,
  `select_difficulty` int NOT NULL,
  `live_id` int NOT NULL,
  `token` varchar(255) DEFAULT NULL, 
  UNIQUE KEY `room_id` (`room_id`)
);
