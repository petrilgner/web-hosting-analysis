CREATE TABLE "webhoster" (
`hoster_domain`	TEXT,
`company`	TEXT,
PRIMARY KEY(hoster_domain)
);
CREATE TABLE "webserver" (
`ip`	VARCHAR(30),
`timestamp`	TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
`as`	VARCHAR(140),
`organization`	VARCHAR(100),
`isp`	VARCHAR(100),
`country`	VARCHAR(10),
`lat`	NUMERIC,
`lon`	NUMERIC,
`city`	INTEGER,
`region`	VARCHAR(40),
`postal_code`	VARCHAR(40),
`contact_email`	VARCHAR(255),
`contact_address`	TEXT,
PRIMARY KEY(`ip`)
);
CREATE TABLE "results" (
`domain`	TEXT,
`timestamp`	INTEGER DEFAULT CURRENT_TIMESTAMP,
`hosted_rev`	NUMERIC,
`hosted_known`	NUMERIC,
`hosted_whois`	NUMERIC,
`hosted_email`	NUMERIC,
`server_httpd`	TEXT,
`server_xpowerer`	TEXT,
`server_type`	TEXT,
`server_ip`	TEXT,
`server_ip_name`	TEXT,
`server_ip_domain`	TEXT,
`dnssec_keyset`	TEXT,
`domain_holdername`	TEXT,
`ip_holdername`	TEXT,
`category`	TEXT,
`original_url`	TEXT,
`note`	TEXT,
`https_support`	NUMERIC,
`ipv6_addr`	TEXT,
PRIMARY KEY(`domain`)
);