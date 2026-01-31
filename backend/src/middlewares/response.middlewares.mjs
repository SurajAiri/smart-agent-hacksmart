function responseFormatter(req, res, next) {
  res.sendResponse = (statusCode, data, message = null, meta = undefined) => {
    if (statusCode < 300) {
      return res.status(statusCode).json({
        statusCode: statusCode,
        data: data,
        meta: meta,
        message: message || "Success",
      });
    }
    return res.status(statusCode).json({
      statusCode: statusCode,
      error: data,
      message: message || "Error",
    });
  };
  next();
}

export { responseFormatter };
