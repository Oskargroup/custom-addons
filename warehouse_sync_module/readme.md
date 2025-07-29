# Warehouse Sync Module v1.3

**Author:** Abolfazl Rezaei
**Category:** Inventory  
**Version:** 1.3  

## Overview

The Warehouse Sync Module is an Odoo addon that synchronizes inventory data between your main warehouse system and Odoo. It automatically fetches product information from an external API and applies intelligent stock rules to maintain optimal inventory levels in your Odoo system.

## Features

### Automated Synchronization
- **Hourly Sync**: Automatically runs every hour via scheduled cron job
- **Manual Sync**: On-demand synchronization through the user interface
- **API Integration**: Connects to external warehouse API for real-time data

### Intelligent Stock Management
- **Dynamic Stock Rules**: Applies different stock levels based on main warehouse quantities:
  - `qty = 0`: Set Odoo stock to 0
  - `30 ≤ qty ≤ 50`: Set Odoo stock to 2
  - `qty < 30`: Set Odoo stock to 0
  - `50 < qty < 200`: Set Odoo stock to 5
  - `qty ≥ 200`: Set Odoo stock to 10

### Alert System
- **Low Stock Alerts**: Automatically flags products with stock < 5
- **Website Publishing**: Disables website sale for low-stock items
- **Detailed Logging**: Tracks all sync operations with comprehensive logs

### Comprehensive Logging
- **Sync History**: Complete record of all synchronization attempts
- **Product Details**: Tracks SKU, barcode, quantities, and alerts
- **Status Tracking**: Success/failure status with detailed messages
- **User Attribution**: Records which user triggered manual syncs

## Installation

1. Copy the module to your Odoo addons directory
2. Update the apps list in Odoo
3. Install the "Warehouse Sync" module
4. The module will automatically set up the cron job for hourly synchronization

## Dependencies

- `stock`: Odoo Inventory Management
- `website_sale`: Odoo eCommerce (for website publishing control)
- `base`: Odoo Base

## Usage

### Accessing the Module

After installation, you'll find the **Warehouse** menu in your Odoo interface with two options:

1. **Manual Sync**: Trigger an immediate synchronization
2. **Sync Logs**: View detailed logs of all sync operations

### Manual Synchronization

1. Navigate to **Warehouse > Manual Sync**
2. Click the menu item to trigger an immediate sync
3. Check **Sync Logs** to verify the operation completed successfully

### Monitoring Sync Operations

1. Go to **Warehouse > Sync Logs**
2. View the list of all sync operations with:
   - Date and time of sync
   - User who triggered the sync
   - Success/failure status
   - Detailed product information
   - Alert status and notes

## Technical Details

### Models

#### `warehouse.sync`
- Main synchronization utility
- Handles API communication and stock updates
- Applies business rules for stock levels

#### `warehouse.sync.log`
- Stores detailed sync operation logs
- Tracks product-level sync information
- Records alerts and status messages

#### `product.template` (Extended)
- Adds `main_warehouse_qty` computed field
- Shows main warehouse quantity on product forms

### API Integration

The module connects to: `https://connect.oskarme.com/api/v1/product/product-details?getAll=true`

**Product Matching**: Products are matched using:
1. SKU (`default_code` field)
2. Barcode (if SKU match not found)

### Cron Job

- **Name**: Warehouse Sync
- **Frequency**: Every 1 hour
- **Method**: `warehouse.sync.run_sync()`
- **Status**: Active by default

## Security

- **Access Rights**: Configured for base users (`base.group_user`)
- **Menu Access**: Available to all users
- **Model Permissions**: Read, Write, Create, Delete access for authorized users

## File Structure

```
warehouse_V1.3/
├── __init__.py
├── __manifest__.py
├── readme.md
├── data/
│   └── cron.xml
├── models/
│   ├── __init__.py
│   ├── warehouse_sync.py
│   └── warehouse_sync_log.py
├── security/
│   └── ir.model.access.csv
└── views/
    └── warehouse_sync_log_views.xml
```

## Troubleshooting

### Common Issues

1. **Sync Failures**: Check the Sync Logs for detailed error messages
2. **API Connection**: Verify network connectivity to the external API
3. **Product Matching**: Ensure products have proper SKU or barcode values
4. **Permissions**: Verify user has appropriate access rights

### Logs Location

All sync operations are logged in **Warehouse > Sync Logs** with detailed information about:
- Success/failure status
- Error messages (if any)
- Product-specific sync details
- Alert notifications

## Support

For technical support or feature requests, please contact the module author.

---

**Note**: This module requires an active internet connection to communicate with the external warehouse API.
