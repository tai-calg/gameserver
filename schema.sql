DROP TABLE IF EXISTS `user`;
DROP TABLE IF EXISTS `room`;
DROP TABLE IF EXISTS `room_user`;
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
  `live_id` int NOT NULL,
  `token` varchar(255) DEFAULT NULL,
  `joined_user_count` int NOT NULL,
  `max_user_count` int NOT NULL,
  `wait_status` int NOT NULL DEFAULT 1,
  UNIQUE KEY `room_id` (`room_id`)
);

CREATE TABLE `room_user` (
  `user_id` bigint NOT NULL,
  `user_name` varchar(255) DEFAULT NULL,
  `leader_card_id` int DEFAULT NULL,
  `select_difficulty` int NOT NULL,
  `is_me` tinyint NOT NULL,
  `is_host` tinyint NOT NULL,
  `room_id` bigint NOT NULL,
  PRIMARY KEY (`room_id`,`user_id`)
);