export * from "./validation.js";


export function validateInventoryForm(data) {
  const errors = {};

  if (!data.name || data.name.trim().length < 3) {
    errors.name = "Item name must be at least 3 characters";
  }

  if (!data.sku || data.sku.trim().length < 2) {
    errors.sku = "SKU is required";
  }

  if (!data.category_id) {
    errors.category_id = "Category is required";
  }

  if (!data.vendor_id) {
    errors.vendor_id = "Vendor is required";
  }

  if (!data.department) {
    errors.department = "Department is required";
  }

  if (!data.unit_price || Number(data.unit_price) < 0.01) {
    errors.unit_price = "Unit price must be greater than 0";
  }

  if (data.quantity_on_hand === "" || Number(data.quantity_on_hand) < 0) {
    errors.quantity_on_hand = "Quantity cannot be negative";
  }

  if (!data.min_stock_level || Number(data.min_stock_level) < 1) {
    errors.min_stock_level = "Minimum stock level must be at least 1";
  }

  if (!data.status) {
    errors.status = "Status is required";
  }

  return errors;
}
export function validateCategoryForm(data) {
  const errors = {};

  if (!data.name || data.name.trim().length < 2) {
    errors.name = "Category name is required";
  }

  return errors;
}

export function validateVendorForm(data) {
  const errors = {};

  if (!data.name || data.name.trim().length < 2) {
    errors.name = "Vendor name is required";
  }

  if (!data.contact_email) {
    errors.contact_email = "Email is required";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.contact_email)) {
    errors.contact_email = "Enter a valid email address";
  }

  if (!data.lead_time_days || Number(data.lead_time_days) < 1) {
    errors.lead_time_days = "Lead time must be at least 1 day";
  }

  return errors;
}
export function validatePurchaseOrderForm(data) {
  const errors = {};

  if (!data.vendor_id) {
    errors.vendor_id = "Vendor is required";
  }

  if (!data.item_id) {
    errors.item_id = "Item is required";
  }

  if (!data.quantity || Number(data.quantity) < 1) {
    errors.quantity = "Quantity must be at least 1";
  }

  if (!data.unit_price || Number(data.unit_price) < 0.01) {
    errors.unit_price = "Unit price must be greater than 0";
  }

  if (!data.expected_date) {
    errors.expected_date = "Expected date is required";
  }

  if (!data.status) {
    errors.status = "Status is required";
  }

  return errors;
}

export function validateStockTransferForm(data) {
  const errors = {};

  if (!data.item_id) {
    errors.item_id = "Item is required";
  }

  if (!data.from_department) {
    errors.from_department = "From department is required";
  }

  if (!data.to_department) {
    errors.to_department = "To department is required";
  }

  if (
    data.from_department &&
    data.to_department &&
    data.from_department === data.to_department
  ) {
    errors.to_department = "From and To departments cannot be same";
  }

  if (!data.quantity || Number(data.quantity) < 1) {
    errors.quantity = "Quantity must be at least 1";
  }

  if (!data.date) {
    errors.date = "Transfer date is required";
  }

  return errors;
}

export function validateStockReceiptForm(data) {
  const errors = {};

  if (!data.vendor_id) {
    errors.vendor_id = "Vendor is required";
  }

  if (!data.item_id) {
    errors.item_id = "Item is required";
  }

  if (!data.quantity || Number(data.quantity) < 1) {
    errors.quantity = "Quantity must be at least 1";
  }

  if (!data.received_date) {
    errors.received_date = "Received date is required";
  }

  if (!data.batch_no || data.batch_no.trim().length < 2) {
    errors.batch_no = "Batch number is required";
  }

  return errors;
}

export function validateUserForm(data, isEdit = false) {
  const errors = {};

  if (!data.name || data.name.trim().length < 2) {
    errors.name = "Name is required";
  }

  if (!data.email) {
    errors.email = "Email is required";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    errors.email = "Enter a valid email address";
  }

  if (!data.role_id) {
    errors.role_id = "Role is required";
  }

  if (!isEdit && (!data.password || data.password.length < 8)) {
    errors.password = "Password must be at least 8 characters";
  }

  return errors;
}

export function validateRoleForm(data) {
  const errors = {};

  if (!data.name || data.name.trim().length < 2) {
    errors.name = "Role name is required";
  }

  if (!Array.isArray(data.permissions) || data.permissions.length === 0) {
    errors.permissions = "Select at least one permission";
  }

  return errors;
}
export function validateSettingsForm(data) {
  const errors = {};

  if (!data.app_name || data.app_name.trim().length < 2) {
    errors.app_name = "Application name is required";
  }

  if (!data.low_stock_threshold || Number(data.low_stock_threshold) < 1) {
    errors.low_stock_threshold = "Low stock threshold must be at least 1";
  }

  if (!data.expiry_alert_days || Number(data.expiry_alert_days) < 1) {
    errors.expiry_alert_days = "Expiry alert days must be at least 1";
  }

  return errors;
}

export function validateProfileForm(data) {
  const errors = {};

  if (!data.name || data.name.trim().length < 2) {
    errors.name = "Name is required";
  }

  if (!data.email) {
    errors.email = "Email is required";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    errors.email = "Enter a valid email";
  }

  return errors;
}

export function validateChangePasswordForm(data) {
  const errors = {};

  if (!data.current_password) {
    errors.current_password = "Current password is required";
  }

  if (!data.new_password || data.new_password.length < 8) {
    errors.new_password = "New password must be at least 8 characters";
  }

  if (data.new_password !== data.confirm_password) {
    errors.confirm_password = "Passwords do not match";
  }

  return errors;
}

export function validateDepartmentForm(data) {
  const errors = {};

  if (!data.name || data.name.trim().length < 2) {
    errors.name = "Department name is required";
  }

  return errors;
}

export function validateReturnForm(data) {
  const errors = {};

  if (!data.item_id) {
    errors.item_id = "Item is required";
  }

  if (!data.quantity || Number(data.quantity) < 1) {
    errors.quantity = "Quantity must be at least 1";
  }

  if (!data.reason || data.reason.trim().length < 3) {
    errors.reason = "Return reason is required";
  }

  return errors;
}