from tensorflow.keras.preprocessing.image import ImageDataGenerator


def data_augmentation(images, masks):

    data_gen_args = dict(
        rotation_range=180,
        width_shift_range=0.3,
        height_shift_range=0.3,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest'
    )


    image_datagen = ImageDataGenerator(**data_gen_args)
    mask_datagen = ImageDataGenerator(**data_gen_args)


    image_datagen.fit(images, augment=True)
    mask_datagen.fit(masks, augment=True)

    seed = 1  # To ensure both generators provide the same augmentation.
    image_generator = image_datagen.flow(images, batch_size=4, seed=seed)
    mask_generator = mask_datagen.flow(masks, batch_size=4, seed=seed)

    print(image_generator.n)
    train_generator = zip(image_generator, mask_generator)

    return train_generator
