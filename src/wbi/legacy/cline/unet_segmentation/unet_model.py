import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, concatenate


def unet_model(input_shape=(512, 512, 1)):

    def down_block(inputs, num_filter):

        c = Conv2D(num_filter, (3, 3), activation='relu', padding='same')(inputs)
        c = Conv2D(num_filter, (3, 3), activation='relu', padding='same')(c)
        p = MaxPooling2D((2, 2), strides=2)(c)

        return p, c
    
    def up_block(inputs, s, num_filter):

        u = UpSampling2D((2, 2))(inputs)
        u = concatenate([u, s])
        c = Conv2D(num_filter, (3, 3), activation='relu', padding='same')(u)
        c = Conv2D(num_filter, (3, 3), activation='relu', padding='same')(c)

        return c

    inputs = Input(input_shape)

    # Contracting path
    p1, c1 = down_block(inputs, 64)
    p2, c2 = down_block(p1, 128)
    p3, c3 = down_block(p2, 256)
    p4, c4 = down_block(p3, 512)

    c5 = Conv2D(1024, (3, 3), activation='relu', padding='same')(p4)
    c5 = Conv2D(1024, (3, 3), activation='relu', padding='same')(c5)
    
    # Expanding path
    c6 = up_block(c5, c4, 512)
    c7 = up_block(c6, c3, 256)
    c8 = up_block(c7, c2, 128)
    c9 = up_block(c8, c1, 64)

    outputs = Conv2D(1, (1, 1), activation='sigmoid')(c9)
    
    model = tf.keras.Model(inputs=[inputs], outputs=[outputs])
    
    return model

