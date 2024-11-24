drop table if exists [dbo].[instrument_categorization]
go

CREATE TABLE [dbo].[instrument_categorization] (
    [instrument_id]      INT          NULL,
    [credit_parent_name] VARCHAR (50) NULL,
    [sector1]            VARCHAR (50) NULL,
    [sector2]            VARCHAR (50) NULL,
    [country]            VARCHAR (50) NULL,
    [currency]           VARCHAR (3)  NULL,
    [ed]                 DATE         NULL
);



-- Insert 50,000 rows into the existing table
DECLARE @counter INT = 1;

WHILE @counter <= 50000
BEGIN
    INSERT INTO [dbo].[instrument_categorization] (
        instrument_id,
        credit_parent_name,
        sector1,
        sector2,
        country,
        currency,
        ed
    )
    VALUES (
        @counter,
        -- Random credit_parent_name
        CASE ABS(CHECKSUM(NEWID())) % 5
            WHEN 0 THEN 'Parent A'
            WHEN 1 THEN 'Parent B'
            WHEN 2 THEN 'Parent C'
            WHEN 3 THEN 'Parent D'
            ELSE 'Parent E'
        END,
        -- Random sector1
        CASE ABS(CHECKSUM(NEWID())) % 5
            WHEN 0 THEN 'Technology'
            WHEN 1 THEN 'Healthcare'
            WHEN 2 THEN 'Finance'
            WHEN 3 THEN 'Energy'
            ELSE 'Consumer Goods'
        END,
        -- Random sector2
        CASE ABS(CHECKSUM(NEWID())) % 5
            WHEN 0 THEN 'Software'
            WHEN 1 THEN 'Biotech'
            WHEN 2 THEN 'Banking'
            WHEN 3 THEN 'Oil & Gas'
            ELSE 'Retail'
        END,
        -- Random country
        CASE ABS(CHECKSUM(NEWID())) % 4
            WHEN 0 THEN 'USA'
            WHEN 1 THEN 'UK'
            WHEN 2 THEN 'Japan'
            ELSE 'Germany'
        END,
        -- Matching random currency
        CASE ABS(CHECKSUM(NEWID())) % 4
            WHEN 0 THEN 'USD'
            WHEN 1 THEN 'GBP'
            WHEN 2 THEN 'JPY'
            ELSE 'EUR'
        END,
        -- Fixed ed
        '2024-11-23'
    );

    SET @counter = @counter + 1;
END;
